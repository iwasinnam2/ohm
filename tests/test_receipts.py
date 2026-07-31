"""Public savings receipts: mint, public view, badge, aggregate stats."""

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from at_utility.redis_store import MemoryStore
from at_utility.metering import Meter
from at_utility.providers import MockProvider
from at_utility.tenants import TenantRegistry
import at_utility.main as main_mod


@pytest.fixture(autouse=True)
async def _mem_state():
    get_settings.cache_clear()
    store = MemoryStore()
    settings = get_settings()
    main_mod.state.settings = settings
    main_mod.state.store = store
    main_mod.state.meter = Meter(store, settings)
    main_mod.state.tenants = TenantRegistry(store, settings)
    main_mod.state.mock = MockProvider()
    main_mod.state.openai = None
    main_mod.state.anthropic = None
    yield
    await store.close()
    get_settings.cache_clear()


async def _warm_cache_hit(client: AsyncClient, headers: dict[str, str]) -> None:
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": "receipt-ping"}],
    }
    await client.post("/v1/chat/completions", headers=headers, json=payload)
    hit = await client.post("/v1/chat/completions", headers=headers, json=payload)
    assert hit.headers.get("x-at-cache") == "HIT"


@pytest.mark.asyncio
async def test_mint_and_read_receipt():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _warm_cache_hit(client, headers)
        minted = await client.post(
            "/v1/savings/receipt",
            headers=headers,
            json={"display_name": "Test Workspace"},
        )
        assert minted.status_code == 200
        body = minted.json()
        token = body["receipt"]["token"]
        assert body["receipt"]["display_name"] == "Test Workspace"
        assert body["receipt"]["estimated_upstream_avoided_usd"] > 0
        assert "_tenant" not in body["receipt"]
        assert body["receipt_url"].endswith(f"/r/{token}")
        assert "badge_markdown" in body

        # Public view requires no auth and never leaks the tenant id.
        public = await client.get(f"/v1/public/receipts/{token}")
        assert public.status_code == 200
        pub = public.json()
        assert pub["receipt"]["display_name"] == "Test Workspace"
        assert "_tenant" not in pub["receipt"]

        badge = await client.get(f"/v1/public/receipts/{token}/badge")
        assert badge.status_code == 200
        shield = badge.json()
        assert shield["schemaVersion"] == 1
        assert shield["message"].startswith("saved $")


@pytest.mark.asyncio
async def test_receipt_unknown_token_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get("/v1/public/receipts/nope-nope-nope")
        assert missing.status_code == 404
        malformed = await client.get("/v1/public/receipts/%2e%2e")
        assert malformed.status_code == 404


@pytest.mark.asyncio
async def test_public_stats_counts_hits():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _warm_cache_hit(client, headers)
        stats = await client.get("/v1/public/stats")
        assert stats.status_code == 200
        body = stats.json()
        assert body["cache_hit_tokens"] > 0
        assert body["estimated_upstream_avoided_usd"] > 0
        assert body["estimate_only"] is True


@pytest.mark.asyncio
async def test_savings_mentions_receipt():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sav = await client.get("/v1/savings", headers=headers)
        assert sav.status_code == 200
        assert sav.json()["receipt"]["mint"] == "POST /v1/savings/receipt"
