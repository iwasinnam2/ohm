"""Phase 1–2: fork / COW / promote / freeze."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.main import app
from tests.app_state import wire_memory_app_state

HEADERS = {"Authorization": "Bearer sk-at-dev"}
CHAT = {"model": "mock", "messages": [{"role": "user", "content": "cow-promote-v1"}]}


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()


def _code(body: dict) -> str:
    return (
        (body.get("error") or {}).get("code")
        or (body.get("detail") or {}).get("code")
        or ""
    )


async def test_fork_list_and_cow_hit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Warm main
        r0 = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert r0.status_code == 200
        assert r0.headers.get("x-at-cache") == "MISS"
        r1 = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
        assert r1.headers.get("x-at-cache") == "HIT"

        fork = await client.post(
            "/v1/cache/trees",
            headers=HEADERS,
            json={"name": "pr-cow"},
        )
        assert fork.status_code == 200
        assert fork.json()["parent_tree_id"] == "main"

        # Child COW-HITs parent warm digest without its own SET
        child = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "pr-cow"},
            json=CHAT,
        )
        assert child.status_code == 200
        assert child.headers.get("x-at-cache") == "HIT"

        listed = await client.get("/v1/cache/trees", headers=HEADERS)
        ids = {t["tree_id"] for t in listed.json()["trees"]}
        assert "main" in ids and "pr-cow" in ids


async def test_promote_merges_child_digests_into_main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/cache/trees", headers=HEADERS, json={"name": "pr-promo"}
        )
        prompt = {
            "model": "mock",
            "messages": [{"role": "user", "content": "promo-child-unique-xyz"}],
        }
        miss = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "pr-promo"},
            json=prompt,
        )
        assert miss.headers.get("x-at-cache") == "MISS"

        promo = await client.post(
            "/v1/cache/trees/pr-promo/promote",
            headers=HEADERS,
            json={},
        )
        assert promo.status_code == 200
        assert promo.json()["digests_copied"] >= 1

        main_hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=prompt
        )
        assert main_hit.headers.get("x-at-cache") == "HIT"


async def test_freeze_blocks_write_allows_hit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/cache/trees", headers=HEADERS, json={"name": "pr-freeze"}
        )
        prompt = {
            "model": "mock",
            "messages": [{"role": "user", "content": "freeze-me"}],
        }
        await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "pr-freeze"},
            json=prompt,
        )
        fr = await client.post(
            "/v1/cache/trees/pr-freeze/freeze", headers=HEADERS
        )
        assert fr.status_code == 200
        assert fr.json()["status"] == "frozen"

        hit = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "pr-freeze"},
            json=prompt,
        )
        assert hit.headers.get("x-at-cache") == "HIT"

        blocked = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Ohm-Cache-Tree": "pr-freeze"},
            json={
                "model": "mock",
                "messages": [{"role": "user", "content": "new-after-freeze"}],
            },
        )
        assert blocked.status_code == 409
        assert _code(blocked.json()) == "tree_frozen"
