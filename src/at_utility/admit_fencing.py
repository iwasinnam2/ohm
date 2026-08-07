"""Digest-bound HIT admit token + optional Redis lease (Tranche 2 / A4).

Flag-off by default (`AT_ADMIT_FENCING=false`). When enabled, the control
plane mints a short-lived HMAC admit token after meter+admit and may take a
Redis lease `admit:{tenant}:{digest}` so concurrent HIT races cannot RELEASE
on a stale admit. The Rust edge verifies the token before serving the body.

Uses the shared edge secret (same material as `X-Ohm-Edge-Secret`) — not the
receipt Ed25519 key — so the edge never needs a second public key.

Counsel note: treat the protocol details here as pre-filing engineering.
Do not blog a deeper RFC until File / Do-not-file binary (see
`docs/ip/04-DISCLOSURE-INVENTORY.md` and `docs/ip/PREFILE-ADMIT-FENCING.md`).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Optional, Protocol


TOKEN_PREFIX = "ohm_admit.v1"
DEFAULT_TTL_SECONDS = 15
DEFAULT_LEASE_TTL_SECONDS = 8


class _StoreNX(Protocol):
    async def set_nx(self, key: str, value: str, ttl_seconds: int) -> bool: ...
    async def get(self, key: str) -> Optional[str]: ...


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def lease_key(tenant_id: str, digest: str) -> str:
    d = (digest or "").strip().lower()
    return f"admit:{(tenant_id or '').strip()}:{d}"


def mint_admit_token(
    *,
    secret: str,
    tenant_id: str,
    request_sha256: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: Optional[int] = None,
    jti: Optional[str] = None,
) -> str:
    """Compact HMAC token bound to tenant + exact-replay digest + expiry."""
    if not (secret or "").strip():
        raise ValueError("admit token requires edge shared secret")
    digest = (request_sha256 or "").strip().lower()
    if not digest:
        raise ValueError("admit token requires request_sha256")
    iat = int(now if now is not None else time.time())
    ttl = max(1, int(ttl_seconds))
    payload: dict[str, Any] = {
        "v": 1,
        "kind": "admit",
        "tenant": tenant_id,
        "digest": digest,
        "iat": iat,
        "exp": iat + ttl,
        "jti": jti or secrets.token_hex(8),
    }
    body = _b64u(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    mac = hmac.new(
        secret.encode("utf-8"),
        f"{TOKEN_PREFIX}.{body}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{TOKEN_PREFIX}.{body}.{_b64u(mac)}"


def verify_admit_token(
    token: str,
    *,
    secret: str,
    request_sha256: str,
    tenant_id: str = "",
    now: Optional[int] = None,
) -> dict[str, Any]:
    """Verify HMAC + digest (+ optional tenant) + expiry. Raises ValueError."""
    if not (secret or "").strip():
        raise ValueError("admit verify requires edge shared secret")
    parts = (token or "").split(".")
    if len(parts) != 4 or f"{parts[0]}.{parts[1]}" != TOKEN_PREFIX:
        raise ValueError("malformed admit token")
    body, mac_b64 = parts[2], parts[3]
    expect = hmac.new(
        secret.encode("utf-8"),
        f"{TOKEN_PREFIX}.{body}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    got = _b64u_decode(mac_b64)
    if not hmac.compare_digest(expect, got):
        raise ValueError("admit token MAC mismatch")
    payload = json.loads(_b64u_decode(body))
    if payload.get("kind") != "admit" or int(payload.get("v") or 0) != 1:
        raise ValueError("admit token kind/v mismatch")
    digest = str(payload.get("digest") or "").lower()
    want = (request_sha256 or "").strip().lower()
    if digest != want:
        raise ValueError("admit token digest mismatch")
    if tenant_id and str(payload.get("tenant") or "") != tenant_id:
        raise ValueError("admit token tenant mismatch")
    exp = int(payload.get("exp") or 0)
    ts = int(now if now is not None else time.time())
    if exp < ts:
        raise ValueError("admit token expired")
    return payload


async def try_acquire_lease(
    store: _StoreNX,
    *,
    tenant_id: str,
    digest: str,
    jti: str,
    ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
) -> bool:
    """SET NX lease. True if this jti owns the lease (new or same jti refresh)."""
    key = lease_key(tenant_id, digest)
    ttl = max(1, int(ttl_seconds))
    if await store.set_nx(key, jti, ttl):
        return True
    existing = await store.get(key)
    return existing == jti
