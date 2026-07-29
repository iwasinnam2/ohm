"""Usage metering for cache hits/misses + fetch SKUs + Stripe meter sync."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from at_utility.config import Settings
from at_utility.redis_store import CacheStore, tenant_key
from at_utility import stripe_billing

log = logging.getLogger("at_utility.meter")


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
    """Stripe meter quantity aligned to AT_PRICE_PER_1K_* (ceil tokens/1000, min 1)."""
    if total_tokens <= 0:
        return 1
    return max(1, math.ceil(total_tokens / 1000.0))


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

    def _sync_stripe(
        self,
        *,
        kind: str,
        value: int | float,
        stripe_customer_id: str,
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
        return stripe_billing.report_meter_event(
            s,
            event_name=event_name,
            stripe_customer_id=stripe_customer_id,
            value=value,
        )

    async def record_chat(
        self,
        tenant: str,
        *,
        cache_hit: bool,
        total_tokens: int,
        stripe_customer_id: str = "",
    ) -> UsageEvent:
        if cache_hit:
            price = self._settings.at_price_per_1k_tokens_hit
            kind = "cache_hit"
        else:
            price = self._settings.at_price_per_1k_tokens_miss
            kind = "cache_miss"
        billed = (total_tokens / 1000.0) * price
        await self._bump(tenant, f"{kind}_tokens", float(total_tokens))
        await self._bump(tenant, f"{kind}_usd", billed)
        await self._bump(tenant, "requests", 1.0)
        # Billable units match AT_PRICE_PER_1K_* meter Prices (ceil tokens/1000)
        units = billable_1k_units(total_tokens)
        synced = self._sync_stripe(
            kind=kind,
            value=units,
            stripe_customer_id=stripe_customer_id,
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
    ) -> UsageEvent:
        billed = count * self._settings.at_price_per_fetch
        await self._bump(tenant, "fetches", float(count))
        await self._bump(tenant, "fetch_usd", billed)
        synced = self._sync_stripe(
            kind="fetch",
            value=count,
            stripe_customer_id=stripe_customer_id,
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
