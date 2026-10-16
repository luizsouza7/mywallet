"""MyWallet 2.0 REST API. Designed for personal use; no real bank credentials."""
import json
import sqlite3
from datetime import date
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from .db import init_db, session
from .importers import MAX_BYTES, parse_statement
from .security import digest, expiry, new_token, now, password_hash, verify_password

app = FastAPI(title="MyWallet 2.0", version="0.1.0")

@app.on_event("startup")
def startup():
    init_db()

class Register(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

class Login(BaseModel):
    email: str
    password: str

class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=70)
    kind: Literal["checking", "savings", "cash"] = "checking"
    opening_balance_cents: int = Field(default=0, ge=-1_000_000_000_00, le=1_000_000_000_00)

class TransactionIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    account_id: int
    amount_cents: int = Field(gt=0, le=1_000_000_000_00)
    direction: Literal["income", "expense"]
    category: str = Field(default="Outros", min_length=1, max_length=60)
    booked_on: date

class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=200)
    account_id: int
    amount_cents: int = Field(gt=0, le=1_000_000_000_00)
    direction: Literal["income", "expense"]
    category: str = Field(min_length=1, max_length=60)
    booked_on: date

def user_id(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Faça login para continuar")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(401, "Sessão inválida")
    with session() as db:
        row = db.execute("""
            SELECT sessions.user_id FROM sessions
            WHERE token_hash=? AND expires_at>?
        """, (digest(token), now())).fetchone()
    if not row:
        raise HTTPException(401, "Sessão expirada ou inválida")
    return row["user_id"]

def owned_account(db, owner, account_id):
    row = db.execute("SELECT id FROM accounts WHERE id=? AND user_id=?", (account_id, owner)).fetchone()
    if not row:
        raise HTTPException(404, "Conta não encontrada")
    return row

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register", status_code=201)
def register(body: Register):
    email = body.email.strip().lower()
    if "@" not in email or email.startswith("@"):
        raise HTTPException(422, "E-mail inválido")
    try:
        with session() as db:
            cursor = db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                                (body.name.strip(), email, password_hash(body.password)))
            # The default account makes onboarding and the first import immediate.
            db.execute("INSERT INTO accounts(user_id,name,kind) VALUES(?,?,?)",
                       (cursor.lastrowid, "Conta principal", "checking"))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "E-mail já cadastrado")
    return {"message": "Conta criada"}

@app.post("/api/auth/login")
def login(body: Login):
    with session() as db:
        row = db.execute("SELECT id,password_hash,name,email FROM users WHERE email=?",
                         (body.email.strip().lower(),)).fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "E-mail ou senha incorretos")
        token = new_token()
        db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                   (digest(token), row["id"], expiry()))
        return {"token": token, "user": {"id": row["id"], "name": row["name"], "email": row["email"]}}

@app.get("/api/auth/me")
def me(owner: int = Depends(user_id)):
    with session() as db:
        return dict(db.execute("SELECT id,name,email FROM users WHERE id=?", (owner,)).fetchone())

@app.post("/api/auth/logout")
def logout(authorization: Annotated[str | None, Header()] = None, owner: int = Depends(user_id)):
    token = (authorization or "")[7:].strip()
    with session() as db:
        db.execute("DELETE FROM sessions WHERE token_hash=? AND user_id=?", (digest(token), owner))
    return {"ok": True}

@app.get("/api/accounts")
def accounts(owner: int = Depends(user_id)):
    with session() as db:
        rows = db.execute("""
            SELECT a.id,a.name,a.kind,a.opening_balance_cents,
                a.opening_balance_cents + COALESCE(SUM(
                    CASE WHEN t.direction='income' THEN t.amount_cents ELSE -t.amount_cents END
                ),0) AS balance_cents
            FROM accounts a LEFT JOIN transactions t ON t.account_id=a.id
            WHERE a.user_id=? GROUP BY a.id ORDER BY a.id
        """, (owner,)).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/accounts", status_code=201)
def create_account(body: AccountIn, owner: int = Depends(user_id)):
    with session() as db:
        cursor = db.execute("""
            INSERT INTO accounts(user_id,name,kind,opening_balance_cents)
            VALUES(?,?,?,?)
        """, (owner, body.name.strip(), body.kind, body.opening_balance_cents))
        return {"id": cursor.lastrowid}

@app.get("/api/transactions")
def transactions(owner: int = Depends(user_id), limit: int = 100, offset: int = 0, account_id: int | None = None):
    if not 1 <= limit <= 500 or not 0 <= offset <= 1_000_000:
        raise HTTPException(422, "Paginação inválida")
    with session() as db:
        if account_id is not None:
            owned_account(db, owner, account_id)
        filters = " AND t.account_id=?" if account_id is not None else ""
        params = (owner, account_id, limit, offset) if account_id is not None else (owner, limit, offset)
        rows = db.execute("""
            SELECT t.id,t.account_id,a.name AS account_name,t.description,
                   t.amount_cents,t.direction,t.category,t.booked_on,
                   t.import_batch_id
            FROM transactions t JOIN accounts a ON a.id=t.account_id
            WHERE t.user_id=?""" + filters + """
            ORDER BY t.booked_on DESC,t.id DESC LIMIT ? OFFSET ?
        """, params).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/transactions", status_code=201)
def create_transaction(body: TransactionIn, owner: int = Depends(user_id)):
    with session() as db:
        owned_account(db, owner, body.account_id)
        cursor = db.execute("""
            INSERT INTO transactions(user_id,account_id,description,amount_cents,direction,category,booked_on)
            VALUES(?,?,?,?,?,?,?)
        """, (owner, body.account_id, body.description.strip(), body.amount_cents,
              body.direction, body.category.strip(), body.booked_on.isoformat()))
        return {"id": cursor.lastrowid}

@app.put("/api/transactions/{transaction_id}")
def update_transaction(transaction_id: int, body: TransactionUpdate, owner: int = Depends(user_id)):
    with session() as db:
        owned_account(db, owner, body.account_id)
        cursor = db.execute("""
            UPDATE transactions SET account_id=?,description=?,amount_cents=?,
            direction=?,category=?,booked_on=? WHERE id=? AND user_id=?
        """, (body.account_id, body.description.strip(), body.amount_cents,
              body.direction, body.category.strip(), body.booked_on.isoformat(), transaction_id, owner))
        if cursor.rowcount != 1:
            raise HTTPException(404, "Movimentação não encontrada")
        return {"ok": True}

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, owner: int = Depends(user_id)):
    with session() as db:
        cursor = db.execute("DELETE FROM transactions WHERE id=? AND user_id=?",
                            (transaction_id, owner))
        if cursor.rowcount != 1:
            raise HTTPException(404, "Movimentação não encontrada")
    return {"ok": True}

@app.get("/api/dashboard")
def dashboard(owner: int = Depends(user_id), month: str | None = None):
    if month:
        try:
            date.fromisoformat(month + "-01")
        except ValueError:
            raise HTTPException(422, "Use YYYY-MM")
    with session() as db:
        row = db.execute("""
            SELECT COALESCE(SUM(opening_balance_cents),0) AS opening
            FROM accounts WHERE user_id=?
        """, (owner,)).fetchone()
        total = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN direction='income' THEN amount_cents
                   ELSE -amount_cents END),0) AS net FROM transactions WHERE user_id=?
        """, (owner,)).fetchone()["net"]
        extra = " AND substr(booked_on,1,7)=?" if month else ""
        params = (owner, month) if month else (owner,)
        stats = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN direction='income' THEN amount_cents ELSE 0 END),0) AS income_cents,
                   COALESCE(SUM(CASE WHEN direction='expense' THEN amount_cents ELSE 0 END),0) AS expense_cents,
                   COUNT(*) AS entries
            FROM transactions WHERE user_id=?""" + extra, params).fetchone()
        categories = db.execute("""
            SELECT category,SUM(amount_cents) AS amount_cents FROM transactions
            WHERE user_id=? AND direction='expense'""" + extra + """
            GROUP BY category ORDER BY amount_cents DESC LIMIT 8
        """, params).fetchall()
        return {"balance_cents": row["opening"] + total,
                "income_cents": stats["income_cents"], "expense_cents": stats["expense_cents"],
                "entries": stats["entries"], "categories": [dict(c) for c in categories]}

async def read_import(owner, account_id, file):
    if not file.filename:
        raise HTTPException(422, "Selecione um arquivo")
    if not file.filename.lower().endswith((".csv", ".ofx")):
        raise HTTPException(422, "Somente arquivos CSV e OFX")
    with session() as db:
        owned_account(db, owner, account_id)
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Arquivo excede 3 MB")
    try:
        return parse_statement(file.filename, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.post("/api/imports/preview")
async def import_preview(account_id: Annotated[int, Form()], file: UploadFile = File(...),
                         owner: int = Depends(user_id)):
    rows, errors = await read_import(owner, account_id, file)
    with session() as db:
        known = {r["fingerprint"] for r in db.execute(
            "SELECT fingerprint FROM transactions WHERE user_id=? AND account_id=? AND fingerprint IS NOT NULL",
            (owner, account_id))}
    return {"rows": [{**row, "duplicate": row["fingerprint"] in known} for row in rows],
            "errors": errors}

@app.post("/api/imports/commit")
async def import_commit(account_id: Annotated[int, Form()], file: UploadFile = File(...),
                        selected_indices: Annotated[str, Form()] = "[]",
                        owner: int = Depends(user_id)):
    rows, errors = await read_import(owner, account_id, file)
    try:
        selected = json.loads(selected_indices)
        if not isinstance(selected, list) or not all(type(i) is int for i in selected):
            raise ValueError()
        if len(selected) != len(set(selected)) or any(i < 0 or i >= len(rows) for i in selected):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "Seleção de transações inválida")
    imported, skipped = 0, 0
    with session() as db:
        owned_account(db, owner, account_id)
        batch = db.execute(
            "INSERT INTO import_batches(user_id,account_id,filename) VALUES(?,?,?)",
            (owner, account_id, file.filename[:150])).lastrowid
        for i in selected:
            item = rows[i]
            cursor = db.execute("""
                INSERT OR IGNORE INTO transactions(
                    user_id,account_id,description,amount_cents,direction,
                    category,booked_on,fingerprint,import_batch_id
                ) VALUES(?,?,?,?,?,?,?,?,?)
            """, (owner, account_id, item["description"], item["amount_cents"],
                  item["direction"], item["category"], item["date"], item["fingerprint"], batch))
            imported += cursor.rowcount
            skipped += 1 - cursor.rowcount
        db.execute("UPDATE import_batches SET inserted_count=? WHERE id=?", (imported, batch))
    return {"imported": imported, "duplicates": skipped, "invalid": len(errors)}

@app.get("/api/imports")
def list_imports(owner: int = Depends(user_id)):
    with session() as db:
        return [dict(r) for r in db.execute("""
            SELECT b.id,b.filename,b.created_at,b.inserted_count,a.name AS account_name
            FROM import_batches b JOIN accounts a ON a.id=b.account_id
            WHERE b.user_id=? ORDER BY b.id DESC LIMIT 30
        """, (owner,)).fetchall()]
