"""Org tenancy, clean ledger, SSO dev-login, policy gate."""

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.main import app


@pytest.mark.asyncio
async def test_org_create_ledger_and_export():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_res = await client.post(
            "/v1/org",
            headers=headers,
            json={
                "name": "Acme Chaos",
                "owner_email": "owner@acme.test",
                "plan": "payg",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert org_res.status_code == 200, org_res.text
        org = org_res.json()["org"]
        assert org["org_id"].startswith("org_")
        assert "default" in org["cost_centers"]

        # Drive two identical mock chats → miss then hit → ledger events
        payload = {
            "model": "mock",
            "messages": [{"role": "user", "content": "ledger-org-ping"}],
        }
        r1 = await client.post("/v1/chat/completions", headers=headers, json=payload)
        r2 = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 200

        led = await client.get("/v1/org/ledger", headers=headers)
        assert led.status_code == 200, led.text
        body = led.json()
        assert body["summary"]["event_count"] >= 1
        assert "by_cost_center" in body["summary"]

        export = await client.get(
            "/v1/org/ledger/export",
            headers=headers,
            params={"format": "csv"},
        )
        assert export.status_code == 200
        assert "event_id" in export.text
        assert "cost_center" in export.text


@pytest.mark.asyncio
async def test_dev_sso_and_audit(monkeypatch):
    from at_utility.main import state
    from at_utility.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("AT_SSO_DEV_SECRET", "dev-sso-secret")
    get_settings.cache_clear()
    # Settings already loaded on state — patch directly for this process.
    state.settings.at_sso_dev_secret = "dev-sso-secret"

    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_res = await client.post(
            "/v1/org",
            headers=headers,
            json={
                "name": "SSO Co",
                "owner_email": "boss@sso.test",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        org_id = org_res.json()["org"]["org_id"]
        login = await client.post(
            "/v1/org/sso/dev-login",
            json={
                "email": "boss@sso.test",
                "org_id": org_id,
                "secret": "dev-sso-secret",
            },
        )
        assert login.status_code == 200, login.text
        token = login.json()["session_token"]
        audit = await client.get(
            "/v1/org/audit",
            headers={"X-Ohm-Session": token},
        )
        assert audit.status_code == 200
        actions = {e["action"] for e in audit.json()["entries"]}
        assert "sso.dev_login" in actions or "org.create" in actions


@pytest.mark.asyncio
async def test_enterprise_sku_delivered_flags():
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/enterprise/skus", headers=headers)
        assert res.status_code == 200
        skus = {s["id"]: s for s in res.json()["skus"]}
        ent = skus["enterprise-dedicated-pool"]
        assert ent["delivered"]["clean_ledger"] is True
        assert ent["delivered"]["sso"] is True
        assert "corporate_clean_ledger" in ent["includes"]
