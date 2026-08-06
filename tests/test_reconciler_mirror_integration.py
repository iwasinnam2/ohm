"""Reconciler -> Postgres mirror integration (skipped unless OHM_DB_TEST_URL is set).

Run locally:  OHM_DB_TEST_URL=postgresql://ohm:ohm@127.0.0.1:5432/ohm pytest -q \
                  tests/test_reconciler_mirror_integration.py
"""
from __future__ import annotations

import os

import pytest

from at_utility.config import get_settings
from at_utility.reconciler import reconcile
from at_utility.redis_store import MemoryStore
from at_utility.tenants import TenantRegistry

DB_URL = os.getenv("OHM_DB_TEST_URL", "")
pytestmark = pytest.mark.skipif(not DB_URL, reason="set OHM_DB_TEST_URL to run")


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_apply_mirrors_account_and_usage_to_postgres(monkeypatch):
    from at_utility.db import mirror

    monkeypatch.setenv("DATABASE_URL", DB_URL)
    monkeypatch.setenv("OHM_DB_ENABLED", "true")
    settings = get_settings()

    store = MemoryStore()
    reg = TenantRegistry(store, settings)
    _, rec = await reg.issue(plan="payg", label="mirror-int")
    # record some usage so a usage_daily row is produced
    from at_utility.metering import Meter

    meter = Meter(store, settings)
    await meter.record_chat(rec.tenant_id, cache_hit=False, total_tokens=120)

    # clean any prior rows for this tenant, then run apply (which mirrors)
    conn = mirror.connect(settings)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM usage_daily WHERE tenant_id=%s", (rec.tenant_id,))
        cur.execute("DELETE FROM accounts WHERE tenant_id=%s", (rec.tenant_id,))
    conn.commit()

    report = await reconcile(store, settings, apply=True)
    assert report.mirrored >= 1

    with conn.cursor() as cur:
        cur.execute("SELECT plan, status FROM accounts WHERE tenant_id=%s", (rec.tenant_id,))
        acct = cur.fetchone()
        cur.execute(
            "SELECT cache_miss_tokens, requests FROM usage_daily WHERE tenant_id=%s",
            (rec.tenant_id,),
        )
        usage = cur.fetchone()
    conn.close()

    assert acct == ("payg", "active")
    assert usage is not None
    assert float(usage[0]) == 120.0  # cache_miss_tokens
    assert float(usage[1]) >= 1.0    # requests
