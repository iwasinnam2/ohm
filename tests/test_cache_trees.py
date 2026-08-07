"""Phase 0 cache trees — select via header/body; isolation; invalid → 400."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.main import app
from tests.app_state import wire_memory_app_state

HEADERS = {"Authorization": "Bearer sk-at-dev"}
CHAT = {"model": "mock", "messages": [{"role": "user", "content": "tree phase0"}]}


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()


async def test_default_tree_miss_then_hit_echoes_main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert r1.status_code == 200
        assert r1.headers.get("x-at-cache") == "MISS"
        assert r1.headers.get("x-ohm-cache-tree") == "main"
        r2 = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert r2.status_code == 200
        assert r2.headers.get("x-at-cache") == "HIT"
        assert r2.headers.get("x-ohm-cache-tree") == "main"


async def test_named_trees_isolated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h_a = {**HEADERS, "X-Ohm-Cache-Tree": "tree-a"}
        h_b = {**HEADERS, "X-Ohm-Cache-Tree": "tree-b"}
        r1 = await client.post("/v1/chat/completions", headers=h_a, json=CHAT)
        assert r1.status_code == 200
        assert r1.headers.get("x-at-cache") == "MISS"
        r2 = await client.post("/v1/chat/completions", headers=h_a, json=CHAT)
        assert r2.headers.get("x-at-cache") == "HIT"
        r3 = await client.post("/v1/chat/completions", headers=h_b, json=CHAT)
        assert r3.status_code == 200
        assert r3.headers.get("x-at-cache") == "MISS"
        assert r3.headers.get("x-ohm-cache-tree") == "tree-b"
        # No ambient bleed: tree-b HIT cannot appear without its own MISS write.
        r4 = await client.post("/v1/chat/completions", headers=h_b, json=CHAT)
        assert r4.headers.get("x-at-cache") == "HIT"
        # Sibling still isolated from a unique prompt only written on tree-a
        unique = {
            "model": "mock",
            "messages": [{"role": "user", "content": "bleed-check-unique-aaa"}],
        }
        await client.post("/v1/chat/completions", headers=h_a, json=unique)
        bleed = await client.post("/v1/chat/completions", headers=h_b, json=unique)
        assert bleed.headers.get("x-at-cache") == "MISS"
        assert bleed.headers.get("x-ohm-cache-tree") == "tree-b"


async def test_invalid_cache_tree_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "BAD TREE"},
            json=CHAT,
        )
        assert res.status_code == 400
        body = res.json()
        code = (
            (body.get("error") or {}).get("code")
            or (body.get("detail") or {}).get("code")
            or body.get("code")
        )
        assert code == "invalid_cache_tree"


async def test_header_wins_over_body():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "from-header"},
            json={**CHAT, "cache_tree": "from-body"},
        )
        assert res.status_code == 200
        assert res.headers.get("x-ohm-cache-tree") == "from-header"


async def test_policy_exposes_cache_tree_stubs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/compliance/policy", headers=HEADERS)
        assert res.status_code == 200
        body = res.json()
        assert body["cache_purpose"] == "identical-request-replay"
        assert body["cache_tree_default"] == "main"
        assert "select" in body["cache_ops"]
