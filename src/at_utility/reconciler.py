"""Periodic reconciler: enforce lazy lifecycle transitions and report billing drift.

The request path only applies some tenant-state changes lazily (a delinquent or
expired tenant is not suspended until its *next* request in ``auth_tenant``). This
sweeper closes that gap by scanning all tenant records and applying the same rules
proactively, plus reporting entropy that needs attention (failed Stripe meter sync,
stale compliance acks).

Safe by default: ``--dry-run`` (the default) only reports. Pass ``--apply`` to make
state changes. All actions reuse ``TenantRegistry`` so behavior matches the gateway.

Run:  python -m at_utility.reconciler [--apply]
"""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from at_utility import stripe_billing
from at_utility.config import Settings, get_settings
from at_utility.redis_store import CacheStore, build_store, tenant_key
from at_utility.tenants import TenantRecord, TenantRegistry

META_PATTERN = "at:*:meta:record"


@dataclass
class Finding:
    tenant_id: str
    reason: str  # expired | delinquent_window | meter_sync_failed | compliance_stale
    detail: str = ""
    applied: bool = False


@dataclass
class Report:
    scanned: int = 0
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    def by_reason(self, reason: str) -> list[Finding]:
        return [f for f in self.findings if f.reason == reason]


def _tenant_id_from_meta_key(key: str) -> Optional[str]:
    # at:{tenant}:meta:record  (tenant ids never contain ':')
    parts = key.split(":")
    if len(parts) == 4 and parts[0] == "at" and parts[2] == "meta" and parts[3] == "record":
        return parts[1]
    return None


async def reconcile(
    store: CacheStore,
    settings: Settings,
    *,
    apply: bool = False,
    now: Optional[int] = None,
) -> Report:
    now = int(time.time()) if now is None else now
    registry = TenantRegistry(store, settings)
    report = Report()

    suspend_days = settings.at_delinquent_suspend_days
    cur_terms = settings.at_compliance_terms_version
    cur_dpa = settings.at_compliance_dpa_version

    for key in await store.scan_keys(META_PATTERN):
        tenant_id = _tenant_id_from_meta_key(key)
        if not tenant_id:
            continue
        raw = await store.get(key)
        if not raw:
            continue
        try:
            rec = TenantRecord.from_json(raw)
        except Exception:  # noqa: BLE001 — skip unparseable records, keep sweeping
            continue
        report.scanned += 1

        suspend_reason: Optional[Finding] = None
        # 1) expiry (design-partner window etc.)
        if rec.status == "active" and rec.is_expired(now):
            suspend_reason = Finding(tenant_id, "expired", f"expires_at={rec.expires_at}")
        # 2) delinquency past the dunning window
        elif (
            rec.status == "active"
            and rec.billing_delinquent_since
            and suspend_days > 0
            and (now - rec.billing_delinquent_since) / 86400.0 >= suspend_days
        ):
            age = (now - rec.billing_delinquent_since) / 86400.0
            suspend_reason = Finding(
                tenant_id, "delinquent_window", f"delinquent_days={age:.1f}>={suspend_days}"
            )
        if suspend_reason is not None:
            if apply:
                updated = await registry.set_status(tenant_id, "suspended")
                suspend_reason.applied = bool(updated)
            report.add(suspend_reason)

        # 3) meter-sync drift (report only — replay is intentionally not automatic to
        #    avoid double-billing; Stripe meters aggregate by sum)
        sync_ok = await store.get(tenant_key(tenant_id, "meter", "stripe_last_ok"))
        if rec.stripe_customer_id and sync_ok == "0":
            report.add(
                Finding(
                    tenant_id,
                    "meter_sync_failed",
                    f"customer={rec.stripe_customer_id} stripe_configured="
                    f"{stripe_billing.stripe_configured(settings)}",
                )
            )

        # 4) compliance ack drift
        if (rec.terms_version and rec.terms_version != cur_terms) or (
            rec.dpa_version and rec.dpa_version != cur_dpa
        ):
            report.add(
                Finding(
                    tenant_id,
                    "compliance_stale",
                    f"terms={rec.terms_version}->{cur_terms} dpa={rec.dpa_version}->{cur_dpa}",
                )
            )

    return report


def _print_report(report: Report, *, apply: bool) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[reconciler:{mode}] scanned {report.scanned} tenant record(s)")
    order = ["expired", "delinquent_window", "meter_sync_failed", "compliance_stale"]
    labels = {
        "expired": "expired -> suspend",
        "delinquent_window": "past dunning window -> suspend",
        "meter_sync_failed": "Stripe meter sync failed (report only)",
        "compliance_stale": "stale terms/DPA ack (report only)",
    }
    for reason in order:
        items = report.by_reason(reason)
        if not items:
            continue
        print(f"  {labels[reason]}: {len(items)}")
        for f in items:
            suffix = " [applied]" if f.applied else (" [would-apply]" if reason in ("expired", "delinquent_window") and not apply else "")
            print(f"    - {f.tenant_id} ({f.detail}){suffix}")
    if not report.findings:
        print("  no findings — fleet is consistent")


async def _run(apply: bool) -> int:
    settings = get_settings()
    store = await build_store(settings)
    try:
        report = await reconcile(store, settings, apply=apply)
    finally:
        await store.close()
    _print_report(report, apply=apply)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="withOhm tenant/billing reconciler")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="apply state changes (suspend expired/delinquent)")
    group.add_argument("--dry-run", action="store_true", help="report only (default)")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(_run(apply=args.apply)))


if __name__ == "__main__":
    main()
