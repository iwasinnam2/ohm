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

        from datetime import datetime, timezone

        month = datetime.now(timezone.utc).strftime("%Y-%m")
        stmt = await client.get(
            "/v1/org/ledger/statement",
            headers=headers,
            params={"month": month},
        )
        assert stmt.status_code == 200, stmt.text
        sbody = stmt.json()
        assert sbody["month"] == month
        assert sbody["timezone"] == "UTC"
        assert sbody["estimate_only"] is True
        assert "by_cost_center" in sbody
        assert sbody["since_ts"] < sbody["until_ts"]
        assert sbody["summary"]["event_count"] >= 1

        bad = await client.get(
            "/v1/org/ledger/statement",
            headers=headers,
            params={"month": "not-a-month"},
        )
        assert bad.status_code == 400


@pytest.mark.asyncio
async def test_path_header_and_hit_ratio():
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": "Bearer sk-at-dev",
        "X-Ohm-Path": "Docs-Bot",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_res = await client.post(
            "/v1/org",
            headers={"Authorization": "Bearer sk-at-dev"},
            json={
                "name": "Path Farm",
                "owner_email": "path@acme.test",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert org_res.status_code == 200, org_res.text

        payload = {
            "model": "mock",
            "messages": [{"role": "user", "content": "hit-ratio-path-ping"}],
        }
        r1 = await client.post("/v1/chat/completions", headers=headers, json=payload)
        r2 = await client.post("/v1/chat/completions", headers=headers, json=payload)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.headers.get("x-ohm-path") == "docs-bot"
        assert r2.headers.get("x-ohm-path") == "docs-bot"
        assert r1.headers.get("x-at-cache", "").upper() == "MISS"
        assert r2.headers.get("x-at-cache", "").upper() == "HIT"

        from datetime import datetime, timezone

        month = datetime.now(timezone.utc).strftime("%Y-%m")
        hr = await client.get(
            "/v1/org/ledger/hit-ratio",
            headers={"Authorization": "Bearer sk-at-dev"},
            params={"month": month, "group_by": "path"},
        )
        assert hr.status_code == 200, hr.text
        body = hr.json()
        assert body["estimate_only"] is True
        assert body["group_by"] == "path"
        assert "docs-bot" in body["groups"]
        g = body["groups"]["docs-bot"]
        assert g["cache_hits"] >= 1
        assert g["cache_misses"] >= 1
        assert g["hit_ratio"] is not None

        thr = await client.get(
            "/v1/ledger/hit-ratio",
            headers={"Authorization": "Bearer sk-at-dev"},
            params={"month": month, "group_by": "path"},
        )
        assert thr.status_code == 200, thr.text
        assert thr.json()["estimate_only"] is True

        bad_path = await client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": "Bearer sk-at-dev",
                "X-Ohm-Path": "!!!bad!!!",
            },
            json={
                "model": "mock",
                "messages": [{"role": "user", "content": "bad-path-norm"}],
            },
        )
        assert bad_path.status_code == 200
        assert bad_path.headers.get("x-ohm-path") == "default"


@pytest.mark.asyncio
async def test_spend_cap_soft_and_hard():
    from at_utility.main import state

    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer sk-at-dev"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_res = await client.post(
            "/v1/org",
            headers=headers,
            json={
                "name": "Cap Co",
                "owner_email": "cap@acme.test",
                "terms_ack": True,
                "dpa_ack": True,
            },
        )
        assert org_res.status_code == 200, org_res.text
        org_id = org_res.json()["org"]["org_id"]

        # Seed month pipe rent above the upcoming cap (HIT-path never gated).
        await state.ledger.append(
            tenant_id="dev",
            org_id=org_id,
            cost_center="default",
            kind="cache_miss",
            pipe_usd=5.0,
            path="ci-prompts",
        )

        pol = await client.put(
            "/v1/org/policy",
            headers=headers,
            json={"spend_cap_usd_month": 1.0, "spend_cap_mode": "soft"},
        )
        assert pol.status_code == 200, pol.text

        miss_payload = {
            "model": "mock",
            "messages": [{"role": "user", "content": "spend-cap-soft-miss"}],
        }
        soft = await client.post(
            "/v1/chat/completions", headers=headers, json=miss_payload
        )
        assert soft.status_code == 200, soft.text
        assert soft.headers.get("x-at-cache", "").upper() == "MISS"
        assert soft.headers.get("x-ohm-spend-cap") == "soft"
        assert soft.headers.get("x-ohm-spend-cap-usd") == "1.00"

        hit = await client.post(
            "/v1/chat/completions", headers=headers, json=miss_payload
        )
        assert hit.status_code == 200
        assert hit.headers.get("x-at-cache", "").upper() == "HIT"

        hard_pol = await client.put(
            "/v1/org/policy",
            headers=headers,
            json={"spend_cap_usd_month": 1.0, "spend_cap_mode": "hard"},
        )
        assert hard_pol.status_code == 200

        blocked = await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={
                "model": "mock",
                "messages": [{"role": "user", "content": "spend-cap-hard-miss"}],
            },
        )
        assert blocked.status_code == 402, blocked.text
        err = blocked.json().get("error") or {}
        assert err.get("code") == "spend_cap_exceeded"

        still_hit = await client.post(
            "/v1/chat/completions", headers=headers, json=miss_payload
        )
        assert still_hit.status_code == 200
        assert still_hit.headers.get("x-at-cache", "").upper() == "HIT"


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
