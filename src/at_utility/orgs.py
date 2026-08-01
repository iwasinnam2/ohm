"""Organization model: SSO tenancy, cost centers, members, service keys."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from at_utility.redis_store import CacheStore


VALID_ROLES = frozenset({"owner", "admin", "member", "service"})


@dataclass
class OrgPolicy:
    """Org-level compliance / routing profile."""

    allowed_purposes: list[str] = field(
        default_factory=lambda: [
            "public_web_retrieval",
            "business_catalog",
            "public_company_info",
            "job_listings",
        ]
    )
    model_allowlist: list[str] = field(default_factory=list)  # empty = all
    fetch_cap_day: int = 0  # 0 = use tenant/plan default
    default_cache_no_store: bool = False
    managed_keys: bool = False  # enterprise managed upstream pool


@dataclass
class OrgRecord:
    org_id: str
    name: str
    plan: str  # payg | enterprise
    created_at: int
    cost_centers: list[str] = field(default_factory=lambda: ["default"])
    members: dict[str, str] = field(default_factory=dict)  # email -> role
    policy: dict[str, Any] = field(default_factory=dict)
    sso_domain: str = ""
    scim_enabled: bool = False
    terms_version: str = ""
    dpa_version: str = ""
    audit_logs: bool = True
    status: str = "active"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "OrgRecord":
        data = json.loads(raw)
        return OrgRecord(
            **{k: data[k] for k in OrgRecord.__dataclass_fields__ if k in data}
        )

    def policy_obj(self) -> OrgPolicy:
        p = self.policy or {}
        return OrgPolicy(
            allowed_purposes=list(
                p.get("allowed_purposes")
                or OrgPolicy().allowed_purposes
            ),
            model_allowlist=list(p.get("model_allowlist") or []),
            fetch_cap_day=int(p.get("fetch_cap_day") or 0),
            default_cache_no_store=bool(p.get("default_cache_no_store") or False),
            managed_keys=bool(p.get("managed_keys") or self.plan == "enterprise"),
        )


class OrgRegistry:
    def __init__(self, store: CacheStore):
        self._store = store

    def _meta(self, org_id: str) -> str:
        return f"at:org:{org_id}:meta"

    def _domain_index(self, domain: str) -> str:
        return f"at:global:org_domain:{domain.lower()}"

    async def get(self, org_id: str) -> Optional[OrgRecord]:
        raw = await self._store.get(self._meta(org_id))
        if not raw:
            return None
        return OrgRecord.from_json(raw)

    async def get_by_domain(self, domain: str) -> Optional[OrgRecord]:
        if not domain:
            return None
        org_id = await self._store.get(self._domain_index(domain))
        if not org_id:
            return None
        return await self.get(org_id)

    async def save(self, org: OrgRecord) -> OrgRecord:
        await self._store.set(self._meta(org.org_id), org.to_json(), ttl_seconds=0)
        if org.sso_domain:
            await self._store.set(
                self._domain_index(org.sso_domain), org.org_id, ttl_seconds=0
            )
        return org

    async def create(
        self,
        *,
        name: str,
        owner_email: str,
        plan: str = "payg",
        sso_domain: str = "",
        terms_version: str = "",
        dpa_version: str = "",
    ) -> OrgRecord:
        org_id = f"org_{uuid.uuid4().hex[:12]}"
        org = OrgRecord(
            org_id=org_id,
            name=name.strip() or org_id,
            plan=plan if plan in ("payg", "enterprise") else "payg",
            created_at=int(time.time()),
            members={owner_email.lower(): "owner"},
            sso_domain=sso_domain.lower().strip(),
            terms_version=terms_version,
            dpa_version=dpa_version,
            policy={
                "managed_keys": plan == "enterprise",
                "allowed_purposes": OrgPolicy().allowed_purposes,
            },
            audit_logs=True,
            scim_enabled=plan == "enterprise",
        )
        return await self.save(org)

    async def add_member(
        self, org_id: str, email: str, role: str = "member"
    ) -> Optional[OrgRecord]:
        org = await self.get(org_id)
        if not org:
            return None
        r = role if role in VALID_ROLES else "member"
        org.members[email.lower()] = r
        return await self.save(org)

    async def set_cost_centers(
        self, org_id: str, centers: list[str]
    ) -> Optional[OrgRecord]:
        org = await self.get(org_id)
        if not org:
            return None
        cleaned = [c.strip() for c in centers if c and c.strip()]
        org.cost_centers = cleaned or ["default"]
        return await self.save(org)

    async def update_policy(
        self, org_id: str, policy: dict[str, Any]
    ) -> Optional[OrgRecord]:
        org = await self.get(org_id)
        if not org:
            return None
        merged = dict(org.policy or {})
        merged.update(policy)
        org.policy = merged
        return await self.save(org)

    def public_view(self, org: OrgRecord) -> dict[str, Any]:
        return {
            "org_id": org.org_id,
            "name": org.name,
            "plan": org.plan,
            "status": org.status,
            "cost_centers": org.cost_centers,
            "member_count": len(org.members),
            "sso_domain": org.sso_domain or None,
            "scim_enabled": org.scim_enabled,
            "audit_logs": org.audit_logs,
            "policy": org.policy_obj().__dict__,
            "terms_version": org.terms_version or None,
            "dpa_version": org.dpa_version or None,
            "created_at": org.created_at,
        }


def new_session_token() -> str:
    return secrets.token_urlsafe(32)
