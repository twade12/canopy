"""Cookie-based auth for CANOPY Vision.

Multi-user: an ``admin`` account is bootstrapped from ``CANOPY_PASSWORD`` on first run,
and the admin creates sub-users (role ``user``) with per-project read/write access. On
login we set a signed, expiring session cookie that carries the user id (HMAC over
``uid.expiry``, keyed by a per-install secret in the data dir). Passwords are stored as
salted PBKDF2-HMAC-SHA256 hashes. With no users and no password the app runs in "open
mode" (local/dev, no login). No external dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from pathlib import Path

COOKIE = "canopy_session"
TTL = 60 * 60 * 24 * 14  # 14 days


def load_secret(data_dir: Path) -> bytes:
    """Load (or create) the per-install signing secret."""
    path = data_dir / "secret.key"
    if path.exists():
        return path.read_bytes()
    data_dir.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    path.write_bytes(key)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key


def make_token(secret: bytes, uid: int, *, ttl: int = TTL) -> str:
    """Create a signed session token for user ``uid`` that expires at now+ttl."""
    base = f"{uid}.{int(time.time()) + ttl}"
    sig = hmac.new(secret, base.encode(), hashlib.sha256).hexdigest()
    return f"{base}.{sig}"


def valid_token(secret: bytes, token: str | None) -> int | None:
    """Return the user id if the session token is valid and unexpired, else None."""
    parts = (token or "").split(".")
    if len(parts) != 3:
        return None
    uid, expiry, sig = parts
    expected = hmac.new(secret, f"{uid}.{expiry}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return int(uid) if int(expiry) > time.time() else None
    except ValueError:
        return None


# --- per-user password hashing (PBKDF2-HMAC-SHA256, salted) ---
def hash_password(password: str, *, rounds: int = 120_000) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds).hex()
    return f"pbkdf2${rounds}${salt}${dk}"


def verify_password(stored: str | None, attempt: str) -> bool:
    if not stored or stored.count("$") != 3:
        return False
    _, rounds, salt, dk = stored.split("$")
    try:
        test = hashlib.pbkdf2_hmac(
            "sha256", (attempt or "").encode(), salt.encode(), int(rounds)).hex()
    except ValueError:
        return False
    return hmac.compare_digest(dk, test)


def check_password(secret_password: str, attempt: str) -> bool:
    return bool(secret_password) and hmac.compare_digest(secret_password, attempt or "")


# --- phone-pairing tokens (scope a phone to one project for a short window) ---
PAIR_TTL = 60 * 60 * 4  # 4 hours


def make_pair_token(secret: bytes, vehicle_id: int, *, ttl: int = PAIR_TTL) -> str:
    base = f"{vehicle_id}.{int(time.time()) + ttl}"
    sig = hmac.new(secret, base.encode(), hashlib.sha256).hexdigest()
    return f"{base}.{sig}"


def valid_pair_token(secret: bytes, token: str | None) -> int | None:
    """Return the vehicle_id if the pairing token is valid and unexpired, else None."""
    parts = (token or "").split(".")
    if len(parts) != 3:
        return None
    vid, expiry, sig = parts
    expected = hmac.new(secret, f"{vid}.{expiry}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return int(vid) if int(expiry) > time.time() else None
    except ValueError:
        return None
