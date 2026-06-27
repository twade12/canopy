"""Minimal cookie-based auth for hosting CANOPY Vision on the public web.

A single shared password (``CANOPY_PASSWORD``) gates the app. On login we set a
signed, expiring session cookie (HMAC over an expiry timestamp, keyed by a per-install
secret persisted in the data dir). No external dependencies, no user database — enough to
keep a public deployment private. Multi-user accounts come later (see docs/GAMEPLAN.md).
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


def make_token(secret: bytes, *, ttl: int = TTL) -> str:
    """Create a signed token that expires at now+ttl."""
    expiry = str(int(time.time()) + ttl)
    sig = hmac.new(secret, expiry.encode(), hashlib.sha256).hexdigest()
    return f"{expiry}.{sig}"


def valid_token(secret: bytes, token: str | None) -> bool:
    """Verify a session token's signature and expiry (constant-time)."""
    if not token or "." not in token:
        return False
    expiry, sig = token.rsplit(".", 1)
    expected = hmac.new(secret, expiry.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        return int(expiry) > time.time()
    except ValueError:
        return False


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
