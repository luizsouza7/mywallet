import pytest
from app.importers import date_iso, money_cents, parse_csv, parse_ofx

@pytest.mark.parametrize("value,expected", [
    ("R$ 1.234,56", 123456), ("-12,50", -1250), ("1,234.56", 123456),
    ("1.234", 123400), ("0.01", 1), ("(14,99)", -1499),
])
def test_money(value, expected):
    assert money_cents(value) == expected

def test_date_formats():
    assert date_iso("15/10/2026") == "2026-10-15"
    assert date_iso("20261015120000") == "2026-10-15"

def test_invalid_values():
    with pytest.raises(ValueError):
        money_cents("abc")
    with pytest.raises(ValueError):
        money_cents("0")
    with pytest.raises(ValueError):
        date_iso("ontem")

def test_csv_separate_credit_debit():
    rows, errors = parse_csv(
        "data;descricao;credito;debito\n15/10/2026;Pix;50,00;\n15/10/2026;Conta;;20,00\n".encode()
    )
    assert len(rows) == 2
    assert not errors
    assert rows[0]["direction"] == "income"
    assert rows[1]["direction"] == "expense"

def test_invalid_csv_rows_are_reported():
    rows, errors = parse_csv(
        b"date,description,amount\n2026-10-15,Coffee,-5.00\nbad,Coffee,-1.00\n"
    )
    assert len(rows) == 1
    assert len(errors) == 1

def test_ofx_fingerprint_stable():
    ofx = b"<STMTTRN><TRNAMT>-12.5<DTPOSTED>20261015<FITID>123<NAME>Market</STMTTRN>"
    first, errors = parse_ofx(ofx)
    second, _ = parse_ofx(ofx)
    assert first[0]["fingerprint"] == second[0]["fingerprint"]
    assert not errors
