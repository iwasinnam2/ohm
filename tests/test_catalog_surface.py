"""Neon-harvested gateway surface: catalog, scopes, lineage, per-model usage."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.catalog import (
    SCOPE_CHAT,
    SCOPE_FETCH,
    has_scope,
    models_json_document,
    models_list_payload,
    normalize_scopes,
)
from at_utility.config import get_settings
from at_utility.main import app
from at_utility.metering import Meter
from at_utility.providers import MockProvider
from at_utility.redis_store import MemoryStore
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


def test_catalog_and_scopes():
    assert has_scope(["ohm:chat"], SCOPE_CHAT)
    assert not has_scope(["ohm:chat"], SCOPE_FETCH)
    assert has_scope(["ohm:admin"], SCOPE_FETCH)  # admin implies all
    assert normalize_scopes(["ohm:fetch", "nope"]) == ["ohm:fetch"]
    payload = models_list_payload()
    assert payload["object"] == "list"
    ids = {m["id"] for m in payload["data"]}
    assert "mock" in ids and "gpt-4o-mini" in ids and "claude-3-5-sonnet-latest" in ids
    doc = models_json_document()
    assert doc["provider"] == "withohm"
    assert "models" in doc


@pytest.mark.asyncio
async def test_public_models_json_and_auth_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pub = await client.get("/models.json")
        assert pub.status_code == 200
        assert pub.json()["provider"] == "withohm"
        models = await client.get(
            "/v1/models", headers={"Authorization": "Bearer sk-at-dev"}
        )
        assert models.status_code == 200
        assert len(models.json()["data"]) >= 3


@pytest.mark.asyncio
async def test_scope_denied_on_fetch_only_key():
    reg = main_mod.state.tenants
    raw, _ = await reg.issue(
        plan="payg",
        terms_version=main_mod.state.settings.at_compliance_terms_version,
        dpa_version=main_mod.state.settings.at_compliance_dpa_version,
        scopes=["ohm:chat"],  # no ohm:fetch
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Chat without fetch OK
        ok = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {raw}"},
            json={"model": "mock", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert ok.status_code == 200
        # Fetch denied
        denied = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {raw}"},
            json={
                "model": "mock",
                "messages": [{"role": "user", "content": "hi"}],
                "fetch_web_context": True,
                "web_urls": ["https://example.com"],
                "web_purpose": "public_web_retrieval",
                "web_compliance_ack": True,
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "scope_denied" or "scope" in str(
            denied.json()
        ).lower()


@pytest.mark.asyncio
async def test_env_lineage_and_parent_suspend():
    reg = main_mod.state.tenants
    s = main_mod.state.settings
    parent_key, parent = await reg.issue(
        plan="payg",
        terms_version=s.at_compliance_terms_version,
        dpa_version=s.at_compliance_dpa_version,
    )
    child_key, child = await reg.issue(
        plan="payg",
        parent_tenant_id=parent.tenant_id,
        env_label="preview",
        terms_version=s.at_compliance_terms_version,
        dpa_version=s.at_compliance_dpa_version,
    )
    assert child.parent_tenant_id == parent.tenant_id
    assert child.env_label == "preview"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {child_key}"},
            json={"model": "mock", "messages": [{"role": "user", "content": "child"}]},
        )
        assert ok.status_code == 200
        await reg.set_status(parent.tenant_id, "suspended")
        blocked = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {child_key}"},
            json={"model": "mock", "messages": [{"role": "user", "content": "child2"}]},
        )
        assert blocked.status_code == 403


@pytest.mark.asyncio
async def test_usage_by_model():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    payload = {
        "model": "mock",
        "messages": [{"role": "user", "content": "meter-by-model"}],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/v1/chat/completions", headers=headers, json=payload)
        await client.post("/v1/chat/completions", headers=headers, json=payload)
        usage = await client.get("/v1/usage", headers=headers)
        assert usage.status_code == 200
        body = usage.json()
        assert "by_model" in body
        assert "mock" in body["by_model"]
        assert body["by_model"]["mock"]["requests"] >= 2
        assert body["by_model"]["mock"]["cache_hit_tokens"] > 0
