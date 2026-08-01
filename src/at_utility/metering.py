"""Usage metering for cache hits/misses + fetch SKUs + Stripe meter sync."""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from at_utility.config import Settings
from at_utility.redis_store import CacheStore, tenant_key
from at_utility import stripe_billing

log = logging.getLogger("at_utility.meter")

# Failed Stripe meter events wait here for replay. Stripe's 24h dedup on the
# event `identifier` makes replay safe even if the original actually landed.
STRIPE_METER_DLQ_KEY = "at:global:stripe_meter_dlq"

# Cross-tenant aggregates powering the public savings counter and receipts.
# Only anonymous totals — never per-tenant data.
GLOBAL_AGG_HIT_TOKENS_KEY = "at:global:agg:cache_hit_tokens"
GLOBAL_AGG_RECEIPTS_KEY = "at:global:agg:receipts_minted"


@dataclass
class UsageEvent:
    tenant: str
    kind: str  # cache_hit | cache_miss | fetch
    tokens: int = 0
    fetches: int = 0
    billed_usd: float = 0.0
    stripe_synced: bool = False
    billable_units: int = 0


def _day_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def billable_1k_units(total_tokens: int) -> int:
    """Stripe meter quantity aligned to AT_PRICE_PER_1K_* (ceil tokens/1000).

    Zero or absent usage bills zero units — never a minimum charge.
    """
    if total_tokens <= 0:
        return 0
    return math.ceil(total_tokens / 1000.0)


class Meter:
    def __init__(self, store: CacheStore, settings: Settings):
        self._store = store
        self._settings = settings

    async def _bump(self, tenant: str, metric: str, amount: float) -> None:
        await self._store.incr_by_float(tenant_key(tenant, "meter", metric), amount)
        day = _day_stamp()
        await self._store.incr_by_float(
            tenant_key(tenant, "ledger", f"{day}:{metric}"), amount
        )

    async def _mark_stripe_sync(self, tenant: str, ok: bool) -> None:
        await self._store.set(
            tenant_key(tenant, "meter", "stripe_last_ok"),
            "1" if ok else "0",
            ttl_seconds=0,
        )
        await self._store.set(
            tenant_key(tenant, "meter", "stripe_last_ts"),
            str(int(time.time())),
            ttl_seconds=0,
        )

    async def _sync_stripe(
        self,
        *,
        kind: str,
        value: int | float,
        stripe_customer_id: str,
        identifier: str = "",
    ) -> bool:
        if not stripe_customer_id:
            return False
        s = self._settings
        event_name = {
            "cache_hit": s.stripe_meter_event_cache_hit,
            "cache_miss": s.stripe_meter_event_cache_miss,
            "fetch": s.stripe_meter_event_web_fetch,
        }.get(kind, "")
        if not event_name:
            return False
        ok = stripe_billing.report_meter_event(
            s,
            event_name=event_name,
            stripe_customer_id=stripe_customer_id,
            value=value,
            identifier=identifier,
        )
        if not ok and s.stripe_secret_key:
            # Stripe is configured but the event failed — dead-letter for replay
            # so a transient outage never silently underbills.
            await self._enqueue_dlq(
                event_name=event_name,
                stripe_customer_id=stripe_customer_id,
                value=value,
                identifier=identifier,
            )
        return ok

    async def _enqueue_dlq(
        self,
        *,
        event_name: str,
        stripe_customer_id: str,
        value: int | float,
        identifier: str,
    ) -> None:
        try:
            await self._store.list_push(
                STRIPE_METER_DLQ_KEY,
                json.dumps(
                    {
                        "event_name": event_name,
                        "stripe_customer_id": stripe_customer_id,
                        "value": value,
                        "identifier": identifier,
                        "ts": int(time.time()),
                    }
                ),
            )
        except Exception as exc:  # noqa: BLE001 — never break chat on DLQ write
            log.error("stripe meter DLQ enqueue failed: %s", exc)

    async def replay_stripe_dlq(self, max_events: int = 100) -> int:
        """Retry dead-lettered Stripe meter events. Returns replayed count.

        Stops at the first failure and re-queues that event — Stripe is likely
        still down, so back off until the next tick. Identifier dedup keeps a
        double-send harmless.
        """
        replayed = 0
        for _ in range(max_events):
            raw = await self._store.list_pop(STRIPE_METER_DLQ_KEY)
            if raw is None:
                break
            try:
                item = json.loads(raw)
            except ValueError:
                log.error("dropping malformed stripe DLQ entry: %.200s", raw)
                continue
            ok = stripe_billing.report_meter_event(
                self._settings,
                event_name=str(item.get("event_name") or ""),
                stripe_customer_id=str(item.get("stripe_customer_id") or ""),
                value=item.get("value") or 0,
                identifier=str(item.get("identifier") or ""),
            )
            if not ok:
                await self._store.list_push(STRIPE_METER_DLQ_KEY, raw)
                break
            replayed += 1
        if replayed:
            log.info("replayed %d stripe meter events from DLQ", replayed)
        return replayed

    async def record_chat(
        self,
        tenant: str,
        *,
        cache_hit: bool,
        total_tokens: int,
        stripe_customer_id: str = "",
        event_id: str = "",
    ) -> UsageEvent:
        if cache_hit:
            price = self._settings.at_price_per_1k_tokens_hit
            kind = "cache_hit"
        else:
            price = self._settings.at_price_per_1k_tokens_miss
            kind = "cache_miss"
        # Billable units match AT_PRICE_PER_1K_* meter Prices (ceil tokens/1000).
        # Ledger USD uses the same math so /v1/usage matches the Stripe invoice.
        units = billable_1k_units(total_tokens)
        billed = units * price
        await self._bump(tenant, f"{kind}_tokens", float(total_tokens))
        await self._bump(tenant, f"{kind}_usd", billed)
        await self._bump(tenant, "requests", 1.0)
        if cache_hit and total_tokens > 0:
            # Anonymous cross-tenant total behind GET /v1/public/stats.
            await self._store.incr_by_float(
                GLOBAL_AGG_HIT_TOKENS_KEY, float(total_tokens)
            )
        synced = False
        if units > 0:
            synced = await self._sync_stripe(
                kind=kind,
                value=units,
                stripe_customer_id=stripe_customer_id,
                identifier=f"{tenant}:{kind}:{event_id or uuid.uuid4().hex}",
            )
            if stripe_customer_id:
                await self._mark_stripe_sync(tenant, synced)
        return UsageEvent(
            tenant=tenant,
            kind=kind,
            tokens=total_tokens,
            billed_usd=billed,
            stripe_synced=synced,
            billable_units=units,
        )

    async def record_fetch(
        self,
        tenant: str,
        count: int = 1,
        stripe_customer_id: str = "",
        event_id: str = "",
    ) -> UsageEvent:
        billed = count * self._settings.at_price_per_fetch
        await self._bump(tenant, "fetches", float(count))
        await self._bump(tenant, "fetch_usd", billed)
        synced = await self._sync_stripe(
            kind="fetch",
            value=count,
            stripe_customer_id=stripe_customer_id,
            identifier=f"{tenant}:fetch:{event_id or uuid.uuid4().hex}",
        )
        if stripe_customer_id:
            await self._mark_stripe_sync(tenant, synced)
        return UsageEvent(
            tenant=tenant,
            kind="fetch",
            fetches=count,
            billed_usd=billed,
            stripe_synced=synced,
            billable_units=count,
        )

    async def mark_receipt_minted(self) -> None:
        await self._store.incr_by_float(GLOBAL_AGG_RECEIPTS_KEY, 1.0)

    async def global_savings(self) -> dict[str, Any]:
        """Anonymous cross-tenant totals for the public counter — no tenant ids."""
        from at_utility.savings import dual_ledger

        hit_raw = await self._store.get(GLOBAL_AGG_HIT_TOKENS_KEY)
        receipts_raw = await self._store.get(GLOBAL_AGG_RECEIPTS_KEY)
        hit_tokens = float(hit_raw) if hit_raw is not None else 0.0
        # Global aggregate has no pipe-rent rollup; ROI stays null.
        ledger = dual_ledger(
            hit_tokens=hit_tokens,
            snap={"revenue_usd": 0.0},
            settings=self._settings,
        )
        return {
            "cache_hit_tokens": hit_tokens,
            "estimated_upstream_avoided_usd": ledger["estimated_upstream_avoided_usd"],
            "estimated_provider_avoided_usd": ledger["estimated_provider_avoided_usd"],
            "estimated_pipe_proxy_avoided_usd": ledger[
                "estimated_pipe_proxy_avoided_usd"
            ],
            "provider_rate_per_1k_tokens": ledger["provider_rate_per_1k_tokens"],
            "receipts_minted": int(float(receipts_raw)) if receipts_raw else 0,
        }

    async def today_fetches(self, tenant: str) -> float:
        day = _day_stamp()
        day_raw = await self._store.get(
            tenant_key(tenant, "ledger", f"{day}:fetches")
        )
        return float(day_raw) if day_raw is not None else 0.0

    async def snapshot(self, tenant: str) -> dict[str, Any]:
        keys = [
            "cache_hit_tokens",
            "cache_miss_tokens",
            "cache_hit_usd",
            "cache_miss_usd",
            "fetches",
            "fetch_usd",
            "requests",
        ]
        out: dict[str, Any] = {
            "tenant": tenant,
            "region": self._settings.at_region,
            "ts": int(time.time()),
            "ledger_day": _day_stamp(),
        }
        for k in keys:
            raw = await self._store.get(tenant_key(tenant, "meter", k))
            out[k] = float(raw) if raw is not None else 0.0
            day_raw = await self._store.get(
                tenant_key(tenant, "ledger", f"{out['ledger_day']}:{k}")
            )
            out[f"today_{k}"] = float(day_raw) if day_raw is not None else 0.0
        hit_usd = out["cache_hit_usd"]
        miss_usd = out["cache_miss_usd"]
        out["arbitrage_gross_usd"] = hit_usd
        out["revenue_usd"] = hit_usd + miss_usd + out["fetch_usd"]
        out["enterprise_monthly_usd"] = self._settings.at_enterprise_monthly_usd
        hit_tok = out["cache_hit_tokens"]
        miss_tok = out["cache_miss_tokens"]
        denom = hit_tok + miss_tok
        out["cache_hit_ratio"] = (hit_tok / denom) if denom > 0 else 0.0
        req = out["requests"]
        out["web_context_attach_rate"] = (
            (out["fetches"] / req) if req > 0 else 0.0
        )
        sync_raw = await self._store.get(tenant_key(tenant, "meter", "stripe_last_ok"))
        sync_ts = await self._store.get(tenant_key(tenant, "meter", "stripe_last_ts"))
        out["stripe_synced"] = sync_raw == "1"
        out["stripe_last_sync_ts"] = int(sync_ts) if sync_ts else None
        out["meter_unit"] = {
            "cache_hit": "per_1k_tokens",
            "cache_miss": "per_1k_tokens",
            "web_fetch": "per_url",
            "list_usd": {
                "cache_hit": self._settings.at_price_per_1k_tokens_hit,
                "cache_miss": self._settings.at_price_per_1k_tokens_miss,
                "web_fetch": self._settings.at_price_per_fetch,
            },
        }
        return out
