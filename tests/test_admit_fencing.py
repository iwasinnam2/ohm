"""Admit token + Redis lease fencing (Tranche 2 / A4), flag-off by default."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

import at_utility.main as main_mod
from at_utility import admit_fencing
from at_utility.main import app
from at_utility.redis_store import MemoryStore
from tests.app_state import wire_memory_app_state

HEADERS = {"Authorization": "Bearer sk-at-dev"}


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()


def test_mint_verify_roundtrip_and_rejects():
    secret = "edge-secret-test"
    digest = "ab" * 32
    token = admit_fencing.mint_admit_token(
        secret=secret,
        tenant_id="tenant_t1",
        request_sha256=digest,
        ttl_seconds=30,
        now=1_700_000_000,
        jti="abc123",
    )
    payload = admit_fencing.verify_admit_token(
        token,
        secret=secret,
        request_sha256=digest,
        tenant_id="tenant_t1",
        now=1_700_000_000,
    )
    assert payload["kind"] == "admit"
    assert payload["jti"] == "abc123"
    assert payload["digest"] == digest

    with pytest.raises(ValueError, match="MAC"):
        admit_fencing.verify_admit_token(
            token[:-4] + "dead",
            secret=secret,
            request_sha256=digest,
            now=1_700_000_000,
        )
    with pytest.raises(ValueError, match="digest"):
        admit_fencing.verify_admit_token(
            token,
            secret=secret,
            request_sha256="cd" * 32,
            now=1_700_000_000,
        )
    with pytest.raises(ValueError, match="expired"):
        admit_fencing.verify_admit_token(
            token,
            secret=secret,
            request_sha256=digest,
            now=1_700_000_000 + 120,
        )


@pytest.mark.asyncio
async def test_lease_nx_fences_second_holder():
    store = MemoryStore()
    ok1 = await admit_fencing.try_acquire_lease(
        store, tenant_id="t1", digest="d" * 64, jti="j1", ttl_seconds=8
    )
    ok2 = await admit_fencing.try_acquire_lease(
        store, tenant_id="t1", digest="d" * 64, jti="j2", ttl_seconds=8
    )
    ok_same = await admit_fencing.try_acquire_lease(
        store, tenant_id="t1", digest="d" * 64, jti="j1", ttl_seconds=8
    )
    assert ok1 is True
    assert ok2 is False
    assert ok_same is True


@pytest.mark.asyncio
async def test_edge_hit_mints_admit_token_when_fencing_on():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    main_mod.state.settings.at_admit_fencing = True
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/internal/edge-hit",
            headers={**HEADERS, "X-Ohm-Edge-Secret": "s3cret"},
            json={
                "total_tokens": 42,
                "model": "mock",
                "request_sha256": "ef" * 32,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["hit_state"] == "RELEASE"
        token = body["admit_token"]
        payload = admit_fencing.verify_admit_token(
            token,
            secret="s3cret",
            request_sha256="ef" * 32,
        )
        assert payload["kind"] == "admit"


@pytest.mark.asyncio
async def test_edge_hit_lease_blocks_concurrent_admit():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    main_mod.state.settings.at_admit_fencing = True
    main_mod.state.settings.at_admit_lease_ttl_seconds = 30
    digest = "aa" * 32
    # Bootstrap key sk-at-dev → tenant_bootstrap_k-at-dev (raw_key[-8:]).
    tenant = "tenant_bootstrap_k-at-dev"
    await admit_fencing.try_acquire_lease(
        main_mod.state.store,
        tenant_id=tenant,
        digest=digest,
        jti="peer",
        ttl_seconds=30,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        blocked = await client.post(
            "/internal/edge-hit",
            headers={**HEADERS, "X-Ohm-Edge-Secret": "s3cret"},
            json={"total_tokens": 1, "model": "mock", "request_sha256": digest},
        )
        assert blocked.status_code == 409
        body = blocked.json()
        err = body.get("error") or {}
        detail = body.get("detail")
        code = err.get("code")
        if not code and isinstance(detail, dict):
            code = detail.get("code")
        assert code == "admit_lease_held"


@pytest.mark.asyncio
async def test_edge_hit_no_token_when_fencing_off():
    main_mod.state.settings.at_edge_shared_secret = "s3cret"
    main_mod.state.settings.at_admit_fencing = False
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/internal/edge-hit",
            headers={**HEADERS, "X-Ohm-Edge-Secret": "s3cret"},
            json={"total_tokens": 10, "request_sha256": "cc" * 32},
        )
        assert res.status_code == 200
        assert "admit_token" not in res.json()
