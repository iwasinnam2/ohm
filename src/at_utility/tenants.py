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
from at_utility.passwords import (
    email_index_key,
    hash_password,
    normalize_email,
    unwrap_api_key,
    verify_password,
    wrap_api_key,
)
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
    status: str  # active | suspended | revoked
    key_prefix: str
    created_at: int
    key_hash: str = ""
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    # True after invoice.paid — the only thing that lifts the soft fetch cap
    billing_paid: bool = False
    # Unix ts when invoice.payment_failed first fired; 0 = not delinquent
    billing_delinquent_since: int = 0
    terms_version: str = ""
    dpa_version: str = ""
    expires_at: int = 0  # unix; 0 = no expiry
    soft_quota_usd: float = 0.0  # 0 = no soft USD cap
    request_cap: int = 0  # 0 = no request cap (metered via Redis separately)
    # Chaos governor: org attribution
    org_id: str = ""
    cost_center: str = "default"
    label: str = ""
    # Account profile (Intermediate email/password login)
    email: str = ""
    password_hash: str = ""
    # Fernet-wrapped sk-at-… so login can restore the bearer (not plaintext at rest)
    api_key_wrapped: str = ""

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

    def _profile_beside_key(self, key_hash: str) -> str:
        """Account details stored beside the apikey SHA-256 index."""
        return f"at:global:apikey:{key_hash}:profile"

    def _account_secret(self) -> str:
        return (
            self._settings.at_account_secret
            or self._settings.at_edge_shared_secret
            or "ohm-local-account-wrap"
        )

    def _tenant_meta(self, tenant_id: str) -> str:
        return tenant_key(tenant_id, "meta", "record")

    def _customer_tenants_key(self, customer_id: str) -> str:
        return f"at:global:stripe_customer:{customer_id}:tenants"

    async def get(self, tenant_id: str) -> Optional[TenantRecord]:
        if not tenant_id:
            return None
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        return TenantRecord.from_json(raw)

    async def resolve(self, raw_key: str) -> Optional[TenantRecord]:
        key_hash = hash_api_key(raw_key)
        # Prefer persisted record (bootstrap keys may be upgraded with org_id).
        tenant_id = await self._store.get(self._key_index(key_hash))
        if tenant_id:
            raw = await self._store.get(self._tenant_meta(tenant_id))
            if raw:
                return TenantRecord.from_json(raw)
        if raw_key in self._settings.api_key_set:
            return TenantRecord(
                tenant_id=f"tenant_bootstrap_{raw_key[-8:]}",
                plan="dev",
                status="active",
                key_prefix=raw_key[:8],
                created_at=0,
                key_hash=key_hash,
                # Local bootstrap inherits current ToS/DPA so MCP need not forge acks.
                terms_version=self._settings.at_compliance_terms_version,
                dpa_version=self._settings.at_compliance_dpa_version,
            )
        return None

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
        org_id: str = "",
        cost_center: str = "default",
        email: str = "",
        password: str = "",
        password_hash: str = "",
    ) -> tuple[str, TenantRecord]:
        tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
        raw_key = f"sk-at-{secrets.token_urlsafe(24)}"
        key_hash = hash_api_key(raw_key)
        resolved_plan = plan if plan in VALID_PLANS else "payg"
        created = int(time.time())
        exp = expires_at
        if resolved_plan == "design_partner" and not exp:
            exp = created + max(1, partner_days) * 86400
        email_n = normalize_email(email)
        if password_hash:
            pw_hash = password_hash
        elif password:
            pw_hash = hash_password(password)
        else:
            pw_hash = ""
        wrapped = wrap_api_key(raw_key, self._account_secret()) if pw_hash else ""
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
            org_id=org_id or "",
            cost_center=(cost_center or "default").strip() or "default",
            label=label or "",
            email=email_n,
            password_hash=pw_hash,
            api_key_wrapped=wrapped,
        )
        payload = record.to_json()
        await self._store.set(self._key_index(key_hash), tenant_id, ttl_seconds=0)
        await self._store.set(self._tenant_meta(tenant_id), payload, ttl_seconds=0)
        await self._write_profile_beside_key(record)
        if email_n and pw_hash:
            await self._store.set(
                email_index_key(email_n), tenant_id, ttl_seconds=0
            )
        if label:
            await self._store.set(
                tenant_key(tenant_id, "meta", "label"), label, ttl_seconds=0
            )
        if org_id:
            await self._store.list_push(
                f"at:org:{org_id}:tenant_ids", tenant_id
            )
        return raw_key, record

    async def _write_profile_beside_key(self, record: TenantRecord) -> None:
        """Persist email + password hash beside the apikey SHA-256 index."""
        if not record.key_hash:
            return
        profile = {
            "email": record.email,
            "password_hash": record.password_hash,
            "tenant_id": record.tenant_id,
            "key_hash": record.key_hash,
            "label": record.label,
            "created_at": record.created_at,
        }
        await self._store.set(
            self._profile_beside_key(record.key_hash),
            json.dumps(profile),
            ttl_seconds=0,
        )

    async def attach_account_credentials(
        self,
        tenant_id: str,
        *,
        email: str,
        password: str,
        raw_key: str,
    ) -> Optional[TenantRecord]:
        """Bind email/password + wrapped key after issue (checkout fulfill)."""
        record = await self.get(tenant_id)
        if not record:
            return None
        email_n = normalize_email(email)
        if not email_n or not password:
            return record
        existing = await self._store.get(email_index_key(email_n))
        if existing and existing != tenant_id:
            raise ValueError("email_already_registered")
        record.email = email_n
        record.password_hash = hash_password(password)
        record.api_key_wrapped = wrap_api_key(raw_key, self._account_secret())
        if not record.key_hash:
            record.key_hash = hash_api_key(raw_key)
        await self._save(record)
        await self._write_profile_beside_key(record)
        await self._store.set(email_index_key(email_n), tenant_id, ttl_seconds=0)
        return record

    async def login_with_password(
        self, email: str, password: str
    ) -> Optional[tuple[str, TenantRecord]]:
        """Verify email/password; return (raw_api_key, record) when valid."""
        email_n = normalize_email(email)
        if not email_n or not password:
            return None
        tenant_id = await self._store.get(email_index_key(email_n))
        if not tenant_id:
            return None
        record = await self.get(tenant_id)
        if not record or record.status != "active":
            return None
        if not verify_password(password, record.password_hash):
            return None
        raw = unwrap_api_key(record.api_key_wrapped, self._account_secret())
        if not raw:
            return None
        return raw, record

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
            await self._index_customer_tenant(customer_id, tenant_id)
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

    async def _index_customer_tenant(self, customer_id: str, tenant_id: str) -> None:
        if not customer_id or not tenant_id:
            return
        existing = await self._store.list_range(
            self._customer_tenants_key(customer_id), 0, -1
        )
        if tenant_id not in existing:
            await self._store.list_push(
                self._customer_tenants_key(customer_id), tenant_id
            )

    async def list_for_customer(self, customer_id: str) -> list[TenantRecord]:
        """All API-key tenants billed to one Stripe customer (account)."""
        if not customer_id:
            return []
        ids = await self._store.list_range(
            self._customer_tenants_key(customer_id), 0, -1
        )
        primary = await self._store.get(f"at:global:stripe_customer:{customer_id}")
        ordered: list[str] = []
        for tid in list(ids) + ([primary] if primary else []):
            if tid and tid not in ordered:
                ordered.append(tid)
        out: list[TenantRecord] = []
        for tid in ordered:
            rec = await self.get(tid)
            if rec and rec.status != "revoked":
                out.append(rec)
        return out

    def _family_key(self, root_tenant_id: str) -> str:
        return f"at:global:key_family:{root_tenant_id}"

    async def _index_family(self, root_tenant_id: str, tenant_id: str) -> None:
        if not root_tenant_id or not tenant_id:
            return
        existing = await self._store.list_range(
            self._family_key(root_tenant_id), 0, -1
        )
        if tenant_id not in existing:
            await self._store.list_push(self._family_key(root_tenant_id), tenant_id)

    async def list_for_family(self, root_tenant_id: str) -> list[TenantRecord]:
        ids = await self._store.list_range(self._family_key(root_tenant_id), 0, -1)
        ordered: list[str] = []
        for tid in list(ids) + [root_tenant_id]:
            if tid and tid not in ordered:
                ordered.append(tid)
        out: list[TenantRecord] = []
        for tid in ordered:
            rec = await self.get(tid)
            if rec and rec.status != "revoked":
                out.append(rec)
        return out

    async def issue_sibling(
        self, parent: TenantRecord, *, label: str = ""
    ) -> tuple[str, TenantRecord]:
        """Mint another key on the same Stripe / org account as ``parent``."""
        raw_key, record = await self.issue(
            plan=parent.plan,
            label=label or parent.label or "additional",
            terms_version=parent.terms_version,
            dpa_version=parent.dpa_version,
            org_id=parent.org_id,
            cost_center=parent.cost_center,
            soft_quota_usd=parent.soft_quota_usd,
            request_cap=parent.request_cap,
        )
        if parent.stripe_customer_id:
            updated = await self.attach_stripe(
                record.tenant_id,
                customer_id=parent.stripe_customer_id,
                subscription_id=parent.stripe_subscription_id,
                plan=parent.plan,
                status="active",
                billing_paid=parent.billing_paid,
            )
            if updated:
                record = updated
        else:
            # Dev/bootstrap seats without Stripe — keep a local family index.
            await self._index_family(parent.tenant_id, parent.tenant_id)
            await self._index_family(parent.tenant_id, record.tenant_id)
        return raw_key, record

    async def revoke(self, tenant_id: str) -> Optional[TenantRecord]:
        """Permanently invalidate a key (hash index removed; status=revoked)."""
        record = await self.get(tenant_id)
        if not record:
            return None
        if record.key_hash:
            await self._store.delete(self._key_index(record.key_hash))
            await self._store.delete(self._profile_beside_key(record.key_hash))
        if record.email:
            await self._store.delete(email_index_key(record.email))
        record.status = "revoked"
        return await self._save(record)

    async def sweep_delinquent(self, suspend_days: int) -> int:
        """Suspend tenants whose dunning window expired, without waiting for
        them to send a request. Returns the number suspended.
        """
        if suspend_days <= 0:
            return 0
        now = int(time.time())
        cutoff_seconds = suspend_days * 86400
        suspended = 0
        keys = await self._store.scan_keys("at:*:meta:record")
        for key in keys:
            raw = await self._store.get(key)
            if not raw:
                continue
            try:
                record = TenantRecord.from_json(raw)
            except (ValueError, TypeError):
                continue
            if (
                record.status == "active"
                and record.billing_delinquent_since
                and now - record.billing_delinquent_since >= cutoff_seconds
            ):
                await self.set_status(record.tenant_id, "suspended")
                suspended += 1
        return suspended

    async def set_cost_center(
        self, tenant_id: str, cost_center: str
    ) -> Optional[TenantRecord]:
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            return None
        record = TenantRecord.from_json(raw)
        record.cost_center = (cost_center or "default").strip() or "default"
        return await self._save(record)

    async def persist(self, record: TenantRecord) -> TenantRecord:
        """Write a (possibly bootstrap/ephemeral) record into Redis."""
        if record.key_hash:
            await self._store.set(
                self._key_index(record.key_hash), record.tenant_id, ttl_seconds=0
            )
        return await self._save(record)

    async def attach_org(
        self, tenant_id: str, org_id: str, *, seed: TenantRecord | None = None
    ) -> Optional[TenantRecord]:
        raw = await self._store.get(self._tenant_meta(tenant_id))
        if not raw:
            if seed is None or seed.tenant_id != tenant_id:
                return None
            record = seed
        else:
            record = TenantRecord.from_json(raw)
        record.org_id = org_id
        await self.persist(record)
        await self._store.list_push(f"at:org:{org_id}:tenant_ids", tenant_id)
        return record

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
            "org_id": record.org_id or None,
            "cost_center": record.cost_center or "default",
            "label": record.label or None,
            "email": record.email or None,
            "has_password": bool(record.password_hash),
        }
