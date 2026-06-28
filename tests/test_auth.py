"""Auth token signing/expiry and password check."""

from __future__ import annotations

from canopy.vision import auth


def test_token_roundtrip_and_tamper() -> None:
    secret = b"x" * 32
    token = auth.make_token(secret, 7)
    assert auth.valid_token(secret, token) == 7             # returns the user id
    assert not auth.valid_token(b"y" * 32, token)          # wrong key
    assert not auth.valid_token(secret, token + "z")        # tampered sig
    assert not auth.valid_token(secret, None)
    assert not auth.valid_token(secret, "garbage")


def test_token_expiry() -> None:
    secret = b"k" * 32
    assert not auth.valid_token(secret, auth.make_token(secret, 1, ttl=-1))


def test_password_check() -> None:
    assert auth.check_password("hunter2", "hunter2")
    assert not auth.check_password("hunter2", "nope")


def test_password_hashing() -> None:
    h = auth.hash_password("s3cret!")
    assert h != "s3cret!" and h.startswith("pbkdf2$")
    assert auth.verify_password(h, "s3cret!")
    assert not auth.verify_password(h, "wrong")
    assert not auth.verify_password(None, "x")
    assert not auth.verify_password("malformed", "x")
    assert not auth.check_password("", "")                  # empty disables (no match)


def test_pair_token() -> None:
    secret = b"p" * 32
    assert auth.valid_pair_token(secret, auth.make_pair_token(secret, 7)) == 7
    assert auth.valid_pair_token(secret, auth.make_pair_token(secret, 7, ttl=-1)) is None
    assert auth.valid_pair_token(b"q" * 32, auth.make_pair_token(secret, 7)) is None  # wrong key
    assert auth.valid_pair_token(secret, "1.999.deadbeef") is None                    # bad sig
    assert auth.valid_pair_token(secret, None) is None
