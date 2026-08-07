"""Password hashing + reversible API-key wrap for account login.

Passwords are never stored plaintext. Issued ``sk-at-…`` secrets are wrapped
with a server-side Fernet key so email/password login can restore the bearer
for the browser seat without re-minting.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

_PBKDF2_ROUNDS = 200_000
_PBKDF2_PREFIX = "pbkdf2_sha256"


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def email_index_key(email: str) -> str:
    dig = hashlib.sha256(normalize_email(email).encode("utf-8")).hexdigest()
    return f"at:global:account_email:{dig}"


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS
    )
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ROUNDS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not password or not stored:
        return False
    try:
        prefix, rounds_s, salt, digest = stored.split("$", 3)
        if prefix != _PBKDF2_PREFIX:
            return False
        rounds = int(rounds_s)
    except (ValueError, TypeError):
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds
    )
    return hmac.compare_digest(dk.hex(), digest)


def _fernet(secret: str) -> Fernet:
    material = (secret or "ohm-local-account-wrap").encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def wrap_api_key(raw_key: str, secret: str) -> str:
    return _fernet(secret).encrypt(raw_key.encode("utf-8")).decode("ascii")


def unwrap_api_key(token: str, secret: str) -> Optional[str]:
    if not token:
        return None
    try:
        return _fernet(secret).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None
