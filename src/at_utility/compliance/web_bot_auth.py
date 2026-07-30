"""Web Bot Auth: RFC 9421 HTTP Message Signatures for OhmBot fetches.

Implements the verified-crawler handshake used by Cloudflare's Verified Bots
program and the licensed-crawl (Pay Per Crawl / Pay Per Use) era: every
outbound fetch can carry `Signature`, `Signature-Input`, and optional
`Signature-Agent` headers signed with an Ed25519 key, so origins can verify
OhmBot's identity instead of treating it as an anonymous scraper.

Signed components follow the web-bot-auth profile: `@authority` (plus
`signature-agent` when a key-directory URL is configured), with parameters
`created`, `expires`, `keyid` (RFC 7638 JWK thumbprint), `alg="ed25519"`,
`nonce`, and `tag="web-bot-auth"`.

Env:
  AT_WEB_BOT_AUTH_ED25519_SEED_B64 — base64(url) 32-byte Ed25519 seed.
    Absent → signing disabled and fetches behave exactly as before.
  AT_WEB_BOT_AUTH_SIGNATURE_AGENT — https URL of the hosted key directory
    (e.g. https://www.withohm.dev/.well-known/http-message-signatures-directory).

Ohm never auto-pays HTTP 402 challenges; payment_required refusals are
surfaced to the caller (see ingest worker) per docs/LEGAL.md.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Optional
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ENV_SEED = "AT_WEB_BOT_AUTH_ED25519_SEED_B64"
ENV_SIGNATURE_AGENT = "AT_WEB_BOT_AUTH_SIGNATURE_AGENT"
TAG = "web-bot-auth"
SIGNATURE_LABEL = "sig1"
DEFAULT_EXPIRES_IN = 300


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def load_signing_key(seed_b64: Optional[str] = None) -> Optional[Ed25519PrivateKey]:
    """Ed25519 key from a base64(url) 32-byte seed; None disables signing."""
    raw = (seed_b64 if seed_b64 is not None else os.getenv(ENV_SEED, "")).strip()
    if not raw:
        return None
    pad = "=" * (-len(raw) % 4)
    try:
        seed = base64.urlsafe_b64decode(raw + pad)
    except Exception:  # noqa: BLE001
        try:
            seed = base64.b64decode(raw + pad)
        except Exception:  # noqa: BLE001
            return None
    if len(seed) != 32:
        return None
    return Ed25519PrivateKey.from_private_bytes(seed)


def signing_enabled() -> bool:
    return load_signing_key() is not None


def public_jwk(key: Ed25519PrivateKey) -> dict[str, str]:
    """Public key as an OKP/Ed25519 JWK (for the hosted key directory)."""
    x = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return {"kty": "OKP", "crv": "Ed25519", "x": _b64u(x)}


def jwk_thumbprint(key: Ed25519PrivateKey) -> str:
    """RFC 7638 JWK thumbprint (base64url SHA-256) — used as `keyid`."""
    jwk = public_jwk(key)
    canonical = json.dumps(
        {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]},
        separators=(",", ":"),
        sort_keys=True,
    )
    return _b64u(hashlib.sha256(canonical.encode("ascii")).digest())


def key_directory(key: Optional[Ed25519PrivateKey] = None) -> Optional[dict]:
    """JWKS payload for /.well-known/http-message-signatures-directory."""
    key = key or load_signing_key()
    if key is None:
        return None
    return {"keys": [public_jwk(key)]}


def authority_for_url(url: str) -> str:
    """RFC 9421 `@authority`: lowercase host, port only when non-default."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    port = parts.port
    default = {"http": 80, "https": 443}.get(parts.scheme or "https")
    if port and port != default:
        return f"{host}:{port}"
    return host


def build_signature_base(
    url: str,
    *,
    signature_agent: str,
    created: int,
    expires: int,
    keyid: str,
    nonce: str,
) -> tuple[str, str]:
    """Return (signature_base, signature_params) per RFC 9421."""
    components = ['"@authority"']
    lines = [f'"@authority": {authority_for_url(url)}']
    if signature_agent:
        components.append('"signature-agent"')
        lines.append(f'"signature-agent": "{signature_agent}"')
    params = (
        f"({' '.join(components)})"
        f";created={created};expires={expires}"
        f';keyid="{keyid}";alg="ed25519";nonce="{nonce}";tag="{TAG}"'
    )
    lines.append(f'"@signature-params": {params}')
    return "\n".join(lines), params


def signature_headers(
    url: str,
    *,
    key: Optional[Ed25519PrivateKey] = None,
    signature_agent: Optional[str] = None,
    created: Optional[int] = None,
    expires_in: int = DEFAULT_EXPIRES_IN,
    nonce: Optional[str] = None,
) -> dict[str, str]:
    """Web Bot Auth headers for a fetch of `url`; {} when signing disabled."""
    key = key or load_signing_key()
    if key is None:
        return {}
    agent = (
        signature_agent
        if signature_agent is not None
        else os.getenv(ENV_SIGNATURE_AGENT, "")
    ).strip()
    created = int(created if created is not None else time.time())
    expires = created + int(expires_in)
    nonce = nonce or _b64u(secrets.token_bytes(32))
    base, params = build_signature_base(
        url,
        signature_agent=agent,
        created=created,
        expires=expires,
        keyid=jwk_thumbprint(key),
        nonce=nonce,
    )
    signature = key.sign(base.encode("utf-8"))
    headers: dict[str, str] = {
        "Signature-Input": f"{SIGNATURE_LABEL}={params}",
        "Signature": f"{SIGNATURE_LABEL}=:{base64.b64encode(signature).decode('ascii')}:",
    }
    if agent:
        headers["Signature-Agent"] = f'"{agent}"'
    return headers
