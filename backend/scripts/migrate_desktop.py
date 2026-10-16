"""Idempotent and opt-in migration of one user's legacy desktop transactions.

Run from backend/:
  python -m scripts.migrate_desktop --legacy-db /path/to/mywallet.db --email user@example.com
  python -m scripts.migrate_desktop --legacy-db /path/to/mywallet.db --email user@example.com --apply

Create a new web account with the same email first. Passwords are NEVER copied.
The legacy database is always opened with SQLite read-only URI.
"""
import argparse
import hashlib
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from app.db import database_path, init_db, session
from app.importers import date_iso

ACCOUNT_NAME = "Importado do MyWallet Desktop"


def load_legacy(path: Path, email: str):
    if not path.is_file():
        raise ValueError("Banco antigo não encontrado")
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as old:
        old.row_factory = sqlite3.Row
        owner = old.execute(
            "SELECT id FROM usuarios WHERE lower(email)=?", (email.lower(),)
        ).fetchone()
        if owner is None:
            raise ValueError("E-mail não encontrado no banco desktop")
        records = old.execute("""
            SELECT id,descricao,valor,categoria,tipo,data FROM movimentacoes
            WHERE usuario_id=? ORDER BY id ASC
        """, (owner["id"],)).fetchall()
        return [dict(r) for r in records]


def prepare(records):
    valid, invalid = [], []
    for r in records:
        try:
            amount = Decimal(str(r["valor"]))
            if not amount.is_finite():
                raise ValueError("Valor não finito")
            cents = int((amount.copy_abs() * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if cents <= 0:
                raise ValueError("Valor zero/negativo inválido")
            if r["tipo"] not in ("receita", "despesa"):
                raise ValueError("Tipo inválido")
            booked = date_iso(r["data"])
            fingerprint = hashlib.sha256(
                ("legacy-desktop|" + str(r["id"])).encode("utf-8")
            ).hexdigest()
            valid.append((
                (str(r["descricao"] or "Movimentação")[:200] or "Movimentação"),
                cents,
                "income" if r["tipo"] == "receita" else "expense",
                (str(r["categoria"] or "Outros")[:60] or "Outros"),
                booked, fingerprint,
            ))
        except (ValueError, InvalidOperation, TypeError) as exc:
            invalid.append((r["id"], str(exc)))
    return valid, invalid


def migrate(legacy_path: Path, email: str, apply=False):
    legacy_path = legacy_path.expanduser().resolve()
    target = database_path().expanduser().resolve()
    if legacy_path == target:
        raise ValueError("O banco antigo e o novo não podem ser o mesmo arquivo")
    records = load_legacy(legacy_path, email)
    valid, invalid = prepare(records)
    if not apply:
        return {"found": len(records), "valid": len(valid), "invalid": invalid,
                "inserted": 0, "dry_run": True}
    init_db()
    inserted = 0
    with session() as db:
        owner = db.execute("SELECT id FROM users WHERE lower(email)=?", (email.lower(),)).fetchone()
        if not owner:
            raise ValueError("Cadastre no MyWallet Web o mesmo e-mail antes de migrar")
        uid = owner["id"]
        account = db.execute(
            "SELECT id FROM accounts WHERE user_id=? AND name=? ORDER BY id LIMIT 1",
            (uid, ACCOUNT_NAME)).fetchone()
        account_id = account["id"] if account else db.execute(
            "INSERT INTO accounts(user_id,name,kind) VALUES(?,?,?)",
            (uid, ACCOUNT_NAME, "checking")).lastrowid
        for desc, cents, direction, category, booked, fingerprint in valid:
            cur = db.execute("""
                INSERT OR IGNORE INTO transactions(
                    user_id,account_id,description,amount_cents,direction,
                    category,booked_on,fingerprint
                ) VALUES (?,?,?,?,?,?,?,?)
            """, (uid, account_id, desc, cents, direction, category, booked, fingerprint))
            inserted += cur.rowcount
    return {"found": len(records), "valid": len(valid),
            "invalid": invalid, "inserted": inserted, "dry_run": False}


def main():
    parser = argparse.ArgumentParser(description="Migrar movimentações do MyWallet desktop para a edição web")
    parser.add_argument("--legacy-db", type=Path, required=True, help="Caminho do SQLite original")
    parser.add_argument("--email", required=True, help="E-mail existente nos dois aplicativos")
    parser.add_argument("--apply", action="store_true", help="Executar gravação no banco novo; padrão é simulação")
    args = parser.parse_args()
    try:
        result = migrate(args.legacy_db, args.email.strip().lower(), args.apply)
    except (ValueError, sqlite3.Error) as exc:
        parser.error(str(exc))
    print("Movimentações encontradas:", result["found"])
    print("Válidas:", result["valid"], "| Inválidas:", len(result["invalid"]))
    print("Inseridas:", result["inserted"])
    if result["invalid"]:
        print("IDs inválidos:", [id for id, _ in result["invalid"]])
    if result["dry_run"]:
        print("SIMULAÇÃO: nenhum dado do MyWallet Web foi alterado. Use --apply para confirmar.")
    else:
        print("Importação concluída. O banco antigo não foi modificado.")


if __name__ == "__main__":
    main()
