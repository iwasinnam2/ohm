"""API key auth (seeded from forex frontend webhook/JWT gating patterns)."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from at_utility.config import Settings


def extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization")
    return parts[1].strip()


def require_api_key(settings: Settings, authorization: str | None = Header(default=None)) -> str:
    key = extract_bearer(authorization)
    if not settings.is_valid_api_key(key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key
