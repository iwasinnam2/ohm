"""Reconciler enforces expiry + dunning suspension and reports drift (MemoryStore)."""
from __future__ import annotations

import time

import pytest

from at_utility.config import get_settings
from at_utility.reconciler import reconcile
from at_utility.redis_store import MemoryStore
from at_utility.tenants import TenantRegistry


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def _seed():
    store = MemoryStore()
    settings = get_settings()
    reg = TenantRegistry(store, settings)
    now = int(time.time())

    # A: healthy, current acks -> no finding
    _, a = await reg.issue(
        plan="payg",
        terms_version=settings.at_compliance_terms_version,
        dpa_version=settings.at_compliance_dpa_version,
    )
    # B: already expired -> expired finding
    _, b = await reg.issue(plan="payg", expires_at=1)
    # C: delinquent beyond the suspend window -> delinquent finding
    _, c = await reg.issue(plan="payg")
    old = now - (settings.at_delinquent_suspend_days + 5) * 86400
    await reg.attach_stripe(c.tenant_id, customer_id="cus_C", billing_delinquent_since=old)
    # C also has a failed meter sync flag -> meter_sync_failed finding
    await store.set(f"at:{c.tenant_id}:meter:stripe_last_ok", "0", ttl_seconds=0)
    # D: stale compliance versions -> compliance_stale finding
    _, d = await reg.issue(plan="payg", terms_version="tos-old", dpa_version="dpa-old")

    return store, settings, reg, {"A": a, "B": b, "C": c, "D": d}


async def _status(store, tenant_id: str) -> str:
    from at_utility.tenants import TenantRecord

    raw = await store.get(f"at:{tenant_id}:meta:record")
    return TenantRecord.from_json(raw).status


@pytest.mark.asyncio
async def test_dry_run_reports_but_does_not_change_state():
    store, settings, _reg, t = await _seed()
    report = await reconcile(store, settings, apply=False)

    assert report.scanned == 4
    assert {f.tenant_id for f in report.by_reason("expired")} == {t["B"].tenant_id}
    assert {f.tenant_id for f in report.by_reason("delinquent_window")} == {t["C"].tenant_id}
    assert {f.tenant_id for f in report.by_reason("meter_sync_failed")} == {t["C"].tenant_id}
    assert {f.tenant_id for f in report.by_reason("compliance_stale")} == {t["D"].tenant_id}
    # dry-run applied nothing
    assert all(f.applied is False for f in report.findings)
    assert await _status(store, t["B"].tenant_id) == "active"
    assert await _status(store, t["C"].tenant_id) == "active"


@pytest.mark.asyncio
async def test_apply_suspends_expired_and_delinquent_only():
    store, settings, _reg, t = await _seed()
    report = await reconcile(store, settings, apply=True)

    assert await _status(store, t["B"].tenant_id) == "suspended"  # expired
    assert await _status(store, t["C"].tenant_id) == "suspended"  # delinquent window
    assert await _status(store, t["A"].tenant_id) == "active"     # healthy untouched
    assert await _status(store, t["D"].tenant_id) == "active"     # compliance drift is report-only
    applied = {f.tenant_id for f in report.findings if f.applied}
    assert applied == {t["B"].tenant_id, t["C"].tenant_id}
