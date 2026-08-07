"""Signed cache-hit receipt tests (X-Ohm-Receipt, docs/RECEIPTS.md)."""

from __future__ import annotations

import base64
import json

import pytest
from httpx import ASGITransport, AsyncClient

import at_utility.main as main_mod
from at_utility import receipts
from at_utility.compliance import web_bot_auth as wba
from at_utility.main import app
from tests.app_state import wire_memory_app_state

RECEIPT_SEED = base64.urlsafe_b64encode(b"\x02" * 32).decode()
BOT_SEED = base64.urlsafe_b64encode(b"\x01" * 32).decode()
HEADERS = {"Authorization": "Bearer sk-at-dev"}
CHAT = {"model": "mock", "messages": [{"role": "user", "content": "receipt me"}]}


@pytest.fixture(autouse=True)
async def _mem_state(monkeypatch):
    monkeypatch.delenv(receipts.ENV_SEED, raising=False)
    monkeypatch.delenv(wba.ENV_SEED, raising=False)
    store = await wire_memory_app_state()
    yield
    await store.close()


def test_disabled_without_seed(monkeypatch):
    monkeypatch.delenv(receipts.ENV_SEED, raising=False)
    assert not receipts.receipts_enabled()
    assert receipts.receipt_public_jwk() is None
    assert (
        receipts.mint_receipt(
            tenant="t",
            model="mock",
            tokens_replayed=10,
            pipe_usd=0.001,
            request_sha256="ab" * 32,
            region="local",
        )
        is None
    )


def test_mint_verify_roundtrip_and_tamper(monkeypatch):
    monkeypatch.setenv(receipts.ENV_SEED, RECEIPT_SEED)
    jws = receipts.mint_receipt(
        tenant="tenant_x",
        model="gpt-4o-mini",
        tokens_replayed=123,
        pipe_usd=0.0000615,
        request_sha256="cd" * 32,
        region="local",
        plane="python",
        created=1_786_000_000,
    )
    assert jws and jws.count(".") == 2
    jwk = receipts.receipt_public_jwk()
    payload = receipts.verify_receipt(jws, jwk)
    assert payload["kind"] == "cache_hit"
    assert payload["tokens_replayed"] == 123
    assert payload["request_sha256"] == "cd" * 32
    assert payload["plane"] == "python"
    assert payload["admit"] == "allow"
    # tenant is fingerprinted, never raw
    assert "tenant_x" not in json.dumps(payload)

    # Tampered payload → signature failure
    head, body, sig = jws.split(".")
    forged = json.loads(
        base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    )
    forged["tokens_replayed"] = 999_999
    forged_b64 = (
        base64.urlsafe_b64encode(
            json.dumps(forged, separators=(",", ":"), sort_keys=True).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    with pytest.raises(Exception):
        receipts.verify_receipt(f"{head}.{forged_b64}.{sig}", jwk)

    # Wrong key → failure
    wrong_jwk = wba.public_jwk(wba.load_signing_key(BOT_SEED))
    with pytest.raises(Exception):
        receipts.verify_receipt(jws, wrong_jwk)


async def test_hit_carries_verifiable_receipt(monkeypatch):
    monkeypatch.setenv(receipts.ENV_SEED, RECEIPT_SEED)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert miss.status_code == 200 and miss.headers["x-at-cache"] == "MISS"
        assert "x-ohm-receipt" not in miss.headers

        hit = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert hit.status_code == 200 and hit.headers["x-at-cache"] == "HIT"
        jws = hit.headers["x-ohm-receipt"]

        # Cold-start verification: resolve the key from the public directory
        directory = await client.get("/.well-known/http-message-signatures-directory")
        assert directory.status_code == 200
        keys = json.loads(directory.text)["keys"]
        payload = receipts.verify_receipt(jws, keys[-1])
        assert payload["kind"] == "cache_hit"
        assert payload["model"] == "mock"
        assert payload["tokens_replayed"] > 0

        # Streamed replay HIT carries the same proof
        stream_hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json={**CHAT, "stream": True}
        )
        assert stream_hit.headers["x-at-cache"] == "HIT"
        receipts.verify_receipt(stream_hit.headers["x-ohm-receipt"], keys[-1])


async def test_hit_without_seed_has_no_receipt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        hit = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert hit.headers["x-at-cache"] == "HIT"
        assert "x-ohm-receipt" not in hit.headers


async def test_directory_serves_both_keys_and_self_signs(monkeypatch):
    monkeypatch.setenv(receipts.ENV_SEED, RECEIPT_SEED)
    monkeypatch.setenv(wba.ENV_SEED, BOT_SEED)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/.well-known/http-message-signatures-directory")
        assert res.status_code == 200
        keys = json.loads(res.text)["keys"]
        assert len(keys) == 2
        assert all(k["kty"] == "OKP" and k["crv"] == "Ed25519" for k in keys)
        assert keys[0] != keys[1]

        # Directory binding (Cloudflare Verified Bots requirement): the
        # response is self-signed, one binding per served key.
        sig_input = res.headers["signature-input"]
        assert sig_input.count('tag="http-message-signatures-directory"') == 2
        assert '("@authority";req)' in sig_input
        assert res.headers["signature"].count(":") >= 4

        # Verify the first binding cryptographically against key 1
        import base64 as b64
        import re

        params = re.search(r"sig1=(\([^)]*\)[^,]*)", sig_input).group(1)
        created = int(re.search(r"created=(\d+)", params).group(1))
        expires = int(re.search(r"expires=(\d+)", params).group(1))
        bot_key = wba.load_signing_key(BOT_SEED)
        base = (
            f'"@authority";req: test\n'
            f'"@signature-params": ("@authority";req);created={created};'
            f'expires={expires};keyid="{wba.jwk_thumbprint(bot_key)}";'
            f'alg="ed25519";tag="http-message-signatures-directory"'
        )
        sig_b64 = re.search(r"sig1=:([^:]+):", res.headers["signature"]).group(1)
        bot_key.public_key().verify(b64.b64decode(sig_b64), base.encode("utf-8"))


async def test_edge_hit_response_includes_receipt(monkeypatch):
    monkeypatch.setenv(receipts.ENV_SEED, RECEIPT_SEED)
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/internal/edge-hit",
            headers={**HEADERS, "X-Ohm-Edge-Secret": "s3cret"},
            json={"total_tokens": 42, "model": "mock", "request_sha256": "ef" * 32},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        payload = receipts.verify_receipt(
            body["receipt"], receipts.receipt_public_jwk()
        )
        assert payload["plane"] == "rust-edge"
        assert payload["tokens_replayed"] == 42
        assert payload["request_sha256"] == "ef" * 32
        assert payload["admit"] == "allow"
        assert payload["meter_event_id"].startswith("cache_hit:")
        assert body["hit_state"] == "RELEASE"
        assert body["meter_event_id"] == payload["meter_event_id"]


async def test_python_hit_exposes_hit_state_and_receipt_bind(monkeypatch):
    monkeypatch.setenv(receipts.ENV_SEED, RECEIPT_SEED)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        miss = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert miss.status_code == 200
        assert miss.headers.get("x-at-cache") == "MISS"
        hit = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache") == "HIT"
        assert hit.headers.get("x-ohm-hit-state") == "RELEASE"
        jws = hit.headers.get("x-ohm-receipt")
        assert jws
        payload = receipts.verify_receipt(jws, receipts.receipt_public_jwk())
        assert payload["admit"] == "allow"
        assert payload["meter_event_id"].startswith("cache_hit:")
        assert payload["plane"] == "python"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/public/honesty")
        assert res.status_code == 200
        body = res.json()
        assert body["limits"] and body["refusals"]
        assert all("claim" in e and "verify" in e for e in body["limits"])
        assert all("claim" in e and "verify" in e for e in body["refusals"])
        assert body["proofs"]["cache_hit_receipts"]["header"] == "X-Ohm-Receipt"
        assert "mid_stream_failover" in json.dumps(body)
        assert "cache trees" in json.dumps(body).lower() or "X-Ohm-Cache-Tree" in json.dumps(
            body
        )
