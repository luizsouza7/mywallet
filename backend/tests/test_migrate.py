import sqlite3

from app.db import init_db, session
from app.security import password_hash
from scripts.migrate_desktop import migrate, ACCOUNT_NAME


def test_desktop_migration_is_readonly_and_idempotent(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy.db"
    new = tmp_path / "new.db"
    monkeypatch.setenv("MYWALLET_DB_PATH", str(new))
    with sqlite3.connect(legacy) as db:
        db.executescript("""
            CREATE TABLE usuarios(id INTEGER PRIMARY KEY,nome TEXT,email TEXT,senha TEXT);
            CREATE TABLE movimentacoes(
              id INTEGER PRIMARY KEY,usuario_id INTEGER,descricao TEXT,valor REAL,
              categoria TEXT,tipo TEXT,data TEXT
            );
            INSERT INTO usuarios VALUES(1,'Original','test@example.com','oldhash');
            INSERT INTO movimentacoes VALUES(5,1,'Supermercado',12.50,'Alimentação','despesa','2026-10-15');
        """)
    assert migrate(legacy, "test@example.com")["valid"] == 1
    assert not new.exists()
    init_db()
    with session() as db:
        db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                   ("Nova pessoa","test@example.com",password_hash("senha-de-teste-123")))
    first = migrate(legacy, "test@example.com", apply=True)
    second = migrate(legacy, "test@example.com", apply=True)
    assert first["inserted"] == 1
    assert second["inserted"] == 0
    with session() as db:
        account = db.execute("SELECT id FROM accounts WHERE name=?", (ACCOUNT_NAME,)).fetchone()
        assert account
        tx = db.execute("SELECT * FROM transactions WHERE account_id=?", (account["id"],)).fetchone()
        assert tx["amount_cents"] == 1250
        assert tx["direction"] == "expense"
    with sqlite3.connect(legacy) as db:
        assert db.execute("SELECT valor FROM movimentacoes WHERE id=5").fetchone()[0] == 12.50
