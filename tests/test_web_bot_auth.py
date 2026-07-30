"""Web Bot Auth (RFC 9421) signing + Pay-Per-Crawl 402 surfacing tests."""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from at_utility.compliance import web_bot_auth as wba

SEED = b"\x01" * 32
SEED_B64 = base64.urlsafe_b64encode(SEED).decode()


def test_signing_disabled_without_seed(monkeypatch):
    monkeypatch.delenv(wba.ENV_SEED, raising=False)
    assert wba.load_signing_key() is None
    assert not wba.signing_enabled()
    assert wba.signature_headers("https://example.com/page") == {}
    assert wba.key_directory() is None


def test_load_signing_key_roundtrip(monkeypatch):
    monkeypatch.setenv(wba.ENV_SEED, SEED_B64)
    key = wba.load_signing_key()
    assert isinstance(key, Ed25519PrivateKey)
    assert wba.signing_enabled()
    jwk = wba.public_jwk(key)
    assert jwk["kty"] == "OKP" and jwk["crv"] == "Ed25519" and jwk["x"]
    # Thumbprint is deterministic
    assert wba.jwk_thumbprint(key) == wba.jwk_thumbprint(wba.load_signing_key())
    assert wba.key_directory() == {"keys": [jwk]}


def test_authority_component():
    assert wba.authority_for_url("https://Example.COM/path?q=1") == "example.com"
    assert wba.authority_for_url("https://example.com:443/x") == "example.com"
    assert wba.authority_for_url("http://example.com:80/x") == "example.com"
    assert wba.authority_for_url("http://example.com:8090/x") == "example.com:8090"


def test_signature_headers_verify(monkeypatch):
    monkeypatch.setenv(wba.ENV_SEED, SEED_B64)
    agent = "https://www.withohm.dev/.well-known/http-message-signatures-directory"
    monkeypatch.setenv(wba.ENV_SIGNATURE_AGENT, agent)

    headers = wba.signature_headers(
        "https://publisher.example/article",
        created=1_753_000_000,
        expires_in=300,
        nonce="test-nonce",
    )
    assert headers["Signature-Agent"] == f'"{agent}"'
    assert headers["Signature-Input"].startswith(
        'sig1=("@authority" "signature-agent");created=1753000000;expires=1753000300;'
    )
    assert ';tag="web-bot-auth"' in headers["Signature-Input"]
    assert ';alg="ed25519"' in headers["Signature-Input"]

    # Reconstruct the signature base exactly as a verifier would and check
    # the Ed25519 signature against the published public key.
    key = wba.load_signing_key()
    base, params = wba.build_signature_base(
        "https://publisher.example/article",
        signature_agent=agent,
        created=1_753_000_000,
        expires=1_753_000_300,
        keyid=wba.jwk_thumbprint(key),
        nonce="test-nonce",
    )
    assert headers["Signature-Input"] == f"sig1={params}"
    assert '"@authority": publisher.example' in base
    sig_b64 = headers["Signature"].removeprefix("sig1=:").removesuffix(":")
    key.public_key().verify(base64.b64decode(sig_b64), base.encode("utf-8"))


def test_refusal_for_status_402_and_403():
    from workers.ingest_worker import _refusal_for_status

    doc = _refusal_for_status(
        "https://paid.example/x", 402, {"crawler-price": "0.01"}, "markdown"
    )
    assert doc is not None and doc["ok"] is False
    assert doc["compliance"]["code"] == "payment_required_402"
    assert doc["compliance"]["pay_per_crawl"] is True
    assert doc["compliance"]["crawler_price"] == "0.01"
    assert doc["markdown"] == ""

    doc = _refusal_for_status("https://blocked.example/x", 403, {}, "json")
    assert doc is not None
    assert doc["compliance"]["code"] == "access_denied_403"
    assert doc["json"] == {}

    assert _refusal_for_status("https://ok.example/x", 200, {}, "markdown") is None
    assert _refusal_for_status("https://err.example/x", 500, {}, "markdown") is None


async def test_httpx_fetch_surfaces_402(monkeypatch):
    import workers.ingest_worker as iw

    class FakeResponse:
        status_code = 402
        headers = {"crawler-price": "0.05", "content-type": "text/plain"}
        url = "https://paid.example/article"
        text = "payment required"

        def raise_for_status(self):
            raise AssertionError("must not raise before 402 handling")

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            # Identified crawler: UA always present
            assert headers and headers.get("User-Agent")
            return FakeResponse()

    monkeypatch.setattr(iw.httpx, "AsyncClient", FakeClient)
    doc = await iw._fetch_via_httpx(
        "https://paid.example/article",
        fmt="markdown",
        redact_pii=True,
        max_chars_per_source=4000,
        respect_robots=True,
    )
    assert doc["ok"] is False
    assert doc["compliance"]["code"] == "payment_required_402"
    assert doc["compliance"]["crawler_price"] == "0.05"
    assert "does not auto-pay" in doc["error"]


async def test_httpx_fetch_sends_signature_headers(monkeypatch):
    import workers.ingest_worker as iw

    monkeypatch.setenv(wba.ENV_SEED, SEED_B64)
    seen: dict = {}

    class FakeResponse:
        status_code = 200
        headers = {}
        url = "https://open.example/page"
        text = "<html><title>t</title><body>hello world</body></html>"

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            seen["headers"] = headers or {}
            return FakeResponse()

    monkeypatch.setattr(iw.httpx, "AsyncClient", FakeClient)

    class AllowedGate:
        allowed = True
        reason = ""
        code = ""

    # gate_url does live DNS (SSRF fail-closed); stub it for the fake host
    monkeypatch.setattr(iw, "gate_url", lambda _u: AllowedGate())
    doc = await iw._fetch_via_httpx(
        "https://open.example/page",
        fmt="markdown",
        redact_pii=True,
        max_chars_per_source=4000,
        respect_robots=True,
    )
    assert doc["ok"] is True
    assert seen["headers"]["Signature"].startswith("sig1=:")
    assert '"@authority"' in seen["headers"]["Signature-Input"]
    assert ';tag="web-bot-auth"' in seen["headers"]["Signature-Input"]


async def test_gateway_key_directory_endpoint(monkeypatch):
    from httpx import ASGITransport, AsyncClient

    from at_utility.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        monkeypatch.delenv(wba.ENV_SEED, raising=False)
        res = await client.get("/.well-known/http-message-signatures-directory")
        assert res.status_code == 404

        monkeypatch.setenv(wba.ENV_SEED, SEED_B64)
        res = await client.get("/.well-known/http-message-signatures-directory")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith(
            "application/http-message-signatures-directory+json"
        )
        keys = json.loads(res.text)["keys"]
        assert keys and keys[0]["kty"] == "OKP" and keys[0]["crv"] == "Ed25519"
