"""Signed cache-hit receipts: the audit pillar made machine-checkable.

Every cache HIT can carry a detached, signed receipt (compact JWS, EdDSA/
Ed25519) proving what the pipe did: which request digest was replayed, how
many upstream tokens were avoided, and what the hit was billed. The public
key is published in the same `/.well-known/http-message-signatures-directory`
JWKS as the Web Bot Auth key, so a skeptic can verify a receipt from a cold
start with nothing but the response header and one public GET.

Env:
  AT_RECEIPT_ED25519_SEED_B64 — base64(url) 32-byte Ed25519 seed, distinct
    from the Web Bot Auth seed (different purpose, independently rotatable).
    Absent → receipts disabled and responses are unchanged.

Receipt shape (JWS payload):
  v, kind ("cache_hit"), iat, region, plane ("python" | "rust-edge"),
  model, tokens_replayed, pipe_usd, request_sha256 (exact-replay identity),
  tenant_sha256 (truncated hash — lets the tenant self-verify without the
  receipt identifying them to third parties).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from at_utility.compliance.web_bot_auth import (
    jwk_thumbprint,
    load_signing_key,
    public_jwk,
)

ENV_SEED = "AT_RECEIPT_ED25519_SEED_B64"
JWS_TYP = "ohm-receipt+jws"
RECEIPT_HEADER = "X-Ohm-Receipt"


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def load_receipt_key(seed_b64: Optional[str] = None) -> Optional[Ed25519PrivateKey]:
    """Dedicated receipt-signing key; None disables receipts."""
    raw = seed_b64 if seed_b64 is not None else os.getenv(ENV_SEED, "")
    return load_signing_key(raw)


def receipts_enabled() -> bool:
    return load_receipt_key() is not None


def receipt_public_jwk() -> Optional[dict[str, str]]:
    key = load_receipt_key()
    if key is None:
        return None
    return public_jwk(key)


def request_digest_from_cache_key(cache_key: str) -> str:
    """`at:{tenant}:cache:{digest}` → digest (the exact-replay identity)."""
    return (cache_key or "").rsplit(":", 1)[-1]


def _tenant_fingerprint(tenant: str) -> str:
    return hashlib.sha256(("ohm-tenant:" + (tenant or "")).encode("utf-8")).hexdigest()[
        :16
    ]


def mint_receipt(
    *,
    tenant: str,
    model: str,
    tokens_replayed: int,
    pipe_usd: float,
    request_sha256: str,
    region: str,
    plane: str = "python",
    kind: str = "cache_hit",
    created: Optional[int] = None,
    key: Optional[Ed25519PrivateKey] = None,
) -> Optional[str]:
    """Compact JWS receipt for a served cache hit; None when disabled."""
    key = key or load_receipt_key()
    if key is None:
        return None
    header = {"alg": "EdDSA", "typ": JWS_TYP, "kid": jwk_thumbprint(key)}
    payload: dict[str, Any] = {
        "v": 1,
        "kind": kind,
        "iat": int(created if created is not None else time.time()),
        "region": region,
        "plane": plane,
        "model": model,
        "tokens_replayed": max(0, int(tokens_replayed)),
        "pipe_usd": round(float(pipe_usd), 6),
        "request_sha256": request_sha256,
        "tenant_sha256": _tenant_fingerprint(tenant),
    }
    signing_input = (
        _b64u(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
        + "."
        + _b64u(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    )
    signature = key.sign(signing_input.encode("ascii"))
    return signing_input + "." + _b64u(signature)


def verify_receipt(jws: str, jwk: dict[str, str]) -> dict[str, Any]:
    """Verify a compact JWS receipt against an OKP/Ed25519 JWK.

    Returns the decoded payload; raises on any signature or shape mismatch.
    """
    if jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519":
        raise ValueError("receipt verification requires an OKP/Ed25519 JWK")
    parts = (jws or "").split(".")
    if len(parts) != 3:
        raise ValueError("not a compact JWS")
    header = json.loads(_b64u_decode(parts[0]))
    if header.get("alg") != "EdDSA":
        raise ValueError(f"unexpected alg {header.get('alg')!r}")
    public = Ed25519PublicKey.from_public_bytes(_b64u_decode(jwk["x"]))
    public.verify(
        _b64u_decode(parts[2]), (parts[0] + "." + parts[1]).encode("ascii")
    )
    return json.loads(_b64u_decode(parts[1]))
