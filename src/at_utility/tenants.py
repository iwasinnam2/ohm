"""Issued tenant API keys stored in Redis (hashed at rest)."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Optional

from at_utility.config import Settings
from at_utility.redis_store import CacheStore, tenant_key

VALID_PLANS = frozenset({"payg", "enterprise", "dev", "design_partner"})
# Default design-partner window (90 days) unless overridden at issue time.
DEFAULT_DESIGN_PARTNER_DAYS = 90


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


@dataclass
class TenantRecord:
    tenant_id: str
    plan: str  # payg | enterprise | dev | design_partner
    status: str  # active | suspended
    key_prefix: str
    created_at: int
    key_hash: str = ""
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    terms_version: str = ""
    dpa_version: str = ""
    expires_at: int = 0  # unix; 0 = no expiry
    soft_quota_usd: float = 0.0  # 0 = no soft USD cap
    request_cap: int = 0  # 0 = no request cap (metered via Redis separately)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "TenantRecord":
        data = json.loads(raw)
        return TenantRecord(
            **{k: data[k] for k in TenantRecord.__dataclass_fields__ if k in data}
        )

    def is_expired(self, now: int | None = None) -> bool:
        if not self.expires_at:
            return False
        return (now if now is not None else int(time.time())) >= self.expires_at


class TenantRegistry:
    def __init__(self, store: CacheStore, settings: Settings):
        self._store = store
        self._settings = settings

    def _key_index(self, key_hash: str) -> str:
        return f"at:global:apikey:{key_hash}"

    def _tenant_meta(self, tenant_id: str) -> str:
        return tenant_key(tenant_id, "meta", "record")

    async def resolve(self, raw_key: str) -> Optional[TenantRecord]:
        if raw_key in self._settings.api_key_set:
            return TenantRecord(
                tenant_id=f"tenant_bootstrap_{raw_key[-8:]}",
                plan="dev",
                status="active",
                key_prefix=raw_key[:8],
                created_at=0,
                key_hash=hash_api_key(raw_key),
            )
        key_hash = hash_api_key(raw_key)
        tenant_id = await self._store.get(self._key_index(key_hash))
        if not tenant_id:
            return None
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        return TenantRecord.from_json(raw)

    async def issue(
        self,
        *,
        plan: str = "payg",
        label: str = "",
        terms_version: str = "",
        dpa_version: str = "",
        expires_at: int = 0,
        soft_quota_usd: float = 0.0,
        request_cap: int = 0,
        partner_days: int = DEFAULT_DESIGN_PARTNER_DAYS,
    ) -> tuple[str, TenantRecord]:
        tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
        raw_key = f"sk-at-{secrets.token_urlsafe(24)}"
        key_hash = hash_api_key(raw_key)
        resolved_plan = plan if plan in VALID_PLANS else "payg"
        created = int(time.time())
        exp = expires_at
        if resolved_plan == "design_partner" and not exp:
            exp = created + max(1, partner_days) * 86400
        record = TenantRecord(
            tenant_id=tenant_id,
            plan=resolved_plan,
            status="active",
            key_prefix=raw_key[:10],
            created_at=created,
            key_hash=key_hash,
            terms_version=terms_version,
            dpa_version=dpa_version,
            expires_at=exp,
            soft_quota_usd=float(soft_quota_usd or 0),
            request_cap=int(request_cap or 0),
        )
        payload = record.to_json()
        await self._store.set(self._key_index(key_hash), tenant_id, ttl_seconds=0)
        await self._store.set(self._tenant_meta(tenant_id), payload, ttl_seconds=0)
        if label:
            await self._store.set(
                tenant_key(tenant_id, "meta", "label"), label, ttl_seconds=0
            )
        return raw_key, record

    async def _save(self, record: TenantRecord) -> TenantRecord:
        await self._store.set(
            self._tenant_meta(record.tenant_id), record.to_json(), ttl_seconds=0
        )
        return record

    async def set_status(self, tenant_id: str, status: str) -> Optional[TenantRecord]:
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        record = TenantRecord.from_json(raw)
        record.status = status
        return await self._save(record)

    async def attach_stripe(
        self,
        tenant_id: str,
        *,
        customer_id: str = "",
        subscription_id: str = "",
        plan: str | None = None,
        status: str | None = None,
    ) -> Optional[TenantRecord]:
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        record = TenantRecord.from_json(raw)
        if customer_id:
            record.stripe_customer_id = customer_id
        if subscription_id:
            record.stripe_subscription_id = subscription_id
        if plan and plan in VALID_PLANS:
            record.plan = plan
        if status:
            record.status = status
        return await self._save(record)

    async def public_view(self, record: TenantRecord) -> dict[str, Any]:
        return {
            "tenant_id": record.tenant_id,
            "plan": record.plan,
            "status": record.status,
            "key_prefix": record.key_prefix,
            "created_at": record.created_at,
            "expires_at": record.expires_at or None,
            "soft_quota_usd": record.soft_quota_usd or None,
            "request_cap": record.request_cap or None,
            "stripe_customer_id": record.stripe_customer_id or None,
            "terms_version": record.terms_version or None,
            "dpa_version": record.dpa_version or None,
        }
