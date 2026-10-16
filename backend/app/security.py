"""PBKDF2 password hashes and hashed opaque session tokens."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

ITERATIONS = 600_000

def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return "pbkdf2_sha256$" + str(ITERATIONS) + "$" + salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt, expected = stored.split("$")
        if algo != "pbkdf2_sha256" or not 200_000 <= int(rounds) <= 1_000_000:
            return False
        value = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(value, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def new_token() -> str:
    return secrets.token_urlsafe(32)

def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def expiry() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
