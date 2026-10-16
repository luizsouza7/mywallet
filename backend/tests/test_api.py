import io

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MYWALLET_DB_PATH", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as c:
        yield c

def register_login(client, email="test@example.com"):
    result = client.post("/api/auth/register", json={
        "name": "Pessoa Teste", "email": email, "password": "uma-senha-forte-1234"})
    assert result.status_code == 201
    logged = client.post("/api/auth/login", json={
        "email": email, "password": "uma-senha-forte-1234"})
    assert logged.status_code == 200
    return {"Authorization": "Bearer " + logged.json()["token"]}

def test_auth_and_password_policy(client):
    weak = client.post("/api/auth/register", json={
        "name": "Ana", "email": "ana@example.com", "password": "1234"})
    assert weak.status_code == 422
    headers = register_login(client)
    assert client.get("/api/auth/me", headers=headers).json()["name"] == "Pessoa Teste"
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/register", json={
        "name": "Repetida", "email": "test@example.com", "password": "uma-senha-forte-1234"}).status_code == 409
    assert client.post("/api/auth/login", json={
        "email": "test@example.com", "password": "errada"}).status_code == 401
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401

def test_accounts_transactions_dashboard_and_ownership(client):
    a = register_login(client, "a@example.com")
    b = register_login(client, "b@example.com")
    account_id = client.get("/api/accounts", headers=a).json()[0]["id"]
    payload = {"description": "Almoço", "account_id": account_id, "amount_cents": 5590,
               "direction": "expense", "category": "Alimentação", "booked_on": "2026-10-15"}
    created = client.post("/api/transactions", headers=a, json=payload)
    assert created.status_code == 201
    tid = created.json()["id"]
    assert client.get("/api/transactions", headers=b).json() == []
    assert client.post("/api/transactions", headers=b, json=payload).status_code == 404
    assert client.put(f"/api/transactions/{tid}", headers=b, json=payload).status_code == 404
    assert client.delete(f"/api/transactions/{tid}", headers=b).status_code == 404
    dashboard = client.get("/api/dashboard?month=2026-10", headers=a).json()
    assert dashboard["balance_cents"] == -5590
    assert dashboard["expense_cents"] == 5590
    assert dashboard["categories"][0]["category"] == "Alimentação"
    assert client.get("/api/dashboard?month=bad", headers=a).status_code == 422
    assert client.put(f"/api/transactions/{tid}", headers=a,
                      json={**payload, "amount_cents": 1200}).status_code == 200
    assert client.get("/api/dashboard", headers=a).json()["balance_cents"] == -1200
    assert client.delete(f"/api/transactions/{tid}", headers=a).status_code == 200
    assert client.get("/api/transactions", headers=a).json() == []

def test_csv_preview_commit_and_idempotency(client):
    headers = register_login(client)
    account_id = client.get("/api/accounts", headers=headers).json()[0]["id"]
    csv = "Data;Descrição;Valor;Categoria\n15/10/2026;Salário;1.500,00;Salário\n15/10/2026;Mercado;-125,47;Alimentação\n".encode("utf-8")
    def upload(path, selected=None):
        data = {"account_id": str(account_id)}
        if selected is not None: data["selected_indices"] = selected
        return client.post(path, headers=headers, data=data,
                           files={"file": ("extrato.csv", io.BytesIO(csv), "text/csv")})
    preview = upload("/api/imports/preview")
    assert preview.status_code == 200, preview.text
    assert [r["amount_cents"] for r in preview.json()["rows"]] == [150000, 12547]
    assert not any(r["duplicate"] for r in preview.json()["rows"])
    first = upload("/api/imports/commit", "[0,1]")
    assert first.status_code == 200, first.text
    assert first.json()["imported"] == 2
    assert upload("/api/imports/commit", "[0,1]").json()["duplicates"] == 2
    assert all(r["duplicate"] for r in upload("/api/imports/preview").json()["rows"])
    assert client.get("/api/dashboard?month=2026-10", headers=headers).json()["balance_cents"] == 137453

def test_identical_csv_rows_remain_distinct(client):
    headers = register_login(client)
    aid = client.get("/api/accounts", headers=headers).json()[0]["id"]
    content = b"date,description,amount\n2026-10-15,Coffee,-5.00\n2026-10-15,Coffee,-5.00\n"
    def commit():
        return client.post("/api/imports/commit", headers=headers,
            data={"account_id": str(aid), "selected_indices": "[0,1]"},
            files={"file": ("test.csv", content, "text/csv")})
    assert commit().json()["imported"] == 2
    assert commit().json()["duplicates"] == 2
    assert len(client.get("/api/transactions", headers=headers).json()) == 2

def test_ofx_and_invalid_files(client):
    headers = register_login(client)
    aid = client.get("/api/accounts", headers=headers).json()[0]["id"]
    ofx = b"<OFX><BANKTRANLIST><STMTTRN><DTPOSTED>20261015000000<TRNAMT>-7.50<FITID>bank-1<NAME>Padaria</STMTTRN></BANKTRANLIST></OFX>"
    response = client.post("/api/imports/preview", headers=headers, data={"account_id": aid},
         files={"file": ("my.ofx", ofx, "application/octet-stream")})
    assert response.status_code == 200, response.text
    assert response.json()["rows"][0]["amount_cents"] == 750
    assert client.post("/api/imports/preview", headers=headers, data={"account_id": aid},
         files={"file": ("evil.exe", b"unknown")}).status_code == 422
    assert client.post("/api/imports/commit", headers=headers,
         data={"account_id": aid, "selected_indices": "[999]"},
         files={"file": ("my.ofx", ofx)}).status_code == 422
    assert client.post("/api/imports/preview", headers=headers, data={"account_id": aid},
         files={"file": ("huge.csv", b"x" * (3 * 1024 * 1024 + 1))}).status_code == 413
