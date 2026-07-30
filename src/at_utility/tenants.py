"""Issued tenant API keys stored in Redis (hashed at rest)."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from at_utility.catalog import DEFAULT_SCOPES, normalize_scopes
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
    # True after invoice.paid (or first metered spend unlocks soft fetch caps)
    billing_paid: bool = False
    # Unix ts when invoice.payment_failed first fired; 0 = not delinquent
    billing_delinquent_since: int = 0
    terms_version: str = ""
    dpa_version: str = ""
    expires_at: int = 0  # unix; 0 = no expiry
    soft_quota_usd: float = 0.0  # 0 = no soft USD cap
    request_cap: int = 0  # 0 = no request cap (metered via Redis separately)
    # Neon-style granular scopes (ohm:chat | ohm:fetch | ohm:admin)
    scopes: list[str] = field(default_factory=lambda: list(DEFAULT_SCOPES))
    # Preview/env lineage: child tenants bind to a parent (analytics + inheritance)
    parent_tenant_id: str = ""
    env_label: str = ""  # e.g. preview, ci, staging

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "TenantRecord":
        data = json.loads(raw)
        rec = TenantRecord(
            **{k: data[k] for k in TenantRecord.__dataclass_fields__ if k in data}
        )
        rec.scopes = normalize_scopes(rec.scopes)
        return rec

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
                # Local bootstrap inherits current ToS/DPA so MCP need not forge acks.
                terms_version=self._settings.at_compliance_terms_version,
                dpa_version=self._settings.at_compliance_dpa_version,
                scopes=list(DEFAULT_SCOPES),
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
        scopes: list[str] | None = None,
        parent_tenant_id: str = "",
        env_label: str = "",
    ) -> tuple[str, TenantRecord]:
        tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
        raw_key = f"sk-at-{secrets.token_urlsafe(24)}"
        key_hash = hash_api_key(raw_key)
        resolved_plan = plan if plan in VALID_PLANS else "payg"
        created = int(time.time())
        exp = expires_at
        if resolved_plan == "design_partner" and not exp:
            exp = created + max(1, partner_days) * 86400

        parent = (parent_tenant_id or "").strip()
        if parent:
            parent_raw = await self._store.get(self._tenant_meta(parent))
            if not parent_raw:
                raise ValueError(f"parent tenant not found: {parent}")
            parent_rec = TenantRecord.from_json(parent_raw)
            # Inherit plan/terms/quotas unless explicitly overridden
            if not terms_version:
                terms_version = parent_rec.terms_version
            if not dpa_version:
                dpa_version = parent_rec.dpa_version
            if soft_quota_usd <= 0 and parent_rec.soft_quota_usd:
                soft_quota_usd = parent_rec.soft_quota_usd
            if request_cap <= 0 and parent_rec.request_cap:
                request_cap = parent_rec.request_cap
            if not exp and parent_rec.expires_at:
                exp = parent_rec.expires_at
            if resolved_plan == "payg" and parent_rec.plan:
                resolved_plan = parent_rec.plan

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
            scopes=normalize_scopes(scopes),
            parent_tenant_id=parent,
            env_label=(env_label or "").strip(),
        )
        payload = record.to_json()
        await self._store.set(self._key_index(key_hash), tenant_id, ttl_seconds=0)
        await self._store.set(self._tenant_meta(tenant_id), payload, ttl_seconds=0)
        if label:
            await self._store.set(
                tenant_key(tenant_id, "meta", "label"), label, ttl_seconds=0
            )
        if parent:
            # Index children for lineage walks (comma-separated id list)
            kids_key = tenant_key(parent, "meta", "children")
            existing = await self._store.get(kids_key)
            kids = [x for x in (existing or "").split(",") if x]
            if tenant_id not in kids:
                kids.append(tenant_id)
            await self._store.set(kids_key, ",".join(kids), ttl_seconds=0)
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

    async def find_by_stripe_customer(
        self, customer_id: str
    ) -> Optional[TenantRecord]:
        """Best-effort scan via Redis label index is unavailable — use meta scan key.

        Tenants store stripe_customer_id on the record; we keep a reverse index.
        """
        if not customer_id:
            return None
        tenant_id = await self._store.get(f"at:global:stripe_customer:{customer_id}")
        if not tenant_id:
            return None
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        return TenantRecord.from_json(raw)

    async def attach_stripe(
        self,
        tenant_id: str,
        *,
        customer_id: str = "",
        subscription_id: str = "",
        plan: str | None = None,
        status: str | None = None,
        billing_paid: bool | None = None,
        billing_delinquent_since: int | None = None,
        clear_delinquent: bool = False,
    ) -> Optional[TenantRecord]:
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        record = TenantRecord.from_json(raw)
        if customer_id:
            record.stripe_customer_id = customer_id
            await self._store.set(
                f"at:global:stripe_customer:{customer_id}",
                tenant_id,
                ttl_seconds=0,
            )
        if subscription_id:
            record.stripe_subscription_id = subscription_id
        if plan and plan in VALID_PLANS:
            record.plan = plan
        if status:
            record.status = status
        if billing_paid is not None:
            record.billing_paid = billing_paid
        if clear_delinquent:
            record.billing_delinquent_since = 0
        elif billing_delinquent_since is not None:
            # Keep the earliest delinquency timestamp
            if not record.billing_delinquent_since:
                record.billing_delinquent_since = billing_delinquent_since
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
            "billing_paid": record.billing_paid,
            "billing_delinquent_since": record.billing_delinquent_since or None,
            "terms_version": record.terms_version or None,
            "dpa_version": record.dpa_version or None,
            "scopes": list(record.scopes or DEFAULT_SCOPES),
            "parent_tenant_id": record.parent_tenant_id or None,
            "env_label": record.env_label or None,
        }
