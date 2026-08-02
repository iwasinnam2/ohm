"""Org console, SSO, ledger export, audit, SCIM — chaos governor HTTP surface."""

from __future__ import annotations

import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field

from at_utility.tenants import TenantRecord

router = APIRouter(tags=["org"])

_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def month_utc_bounds(month: str) -> tuple[int, int]:
    """Return [since_ts, until_ts) UTC bounds for YYYY-MM."""
    m = _MONTH_RE.match(month or "")
    if not m:
        raise HTTPException(
            status_code=400, detail="month must be YYYY-MM (UTC calendar month)"
        )
    year, mon = int(m.group(1)), int(m.group(2))
    if mon < 1 or mon > 12:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


def _state():
    from at_utility import main as gateway

    return gateway.state


async def auth_tenant(
    authorization: str | None = Header(default=None),
) -> tuple[str, TenantRecord]:
    from at_utility import main as gateway

    return await gateway.auth_tenant(authorization)


async def auth_org_session(
    x_ohm_session: str | None = Header(default=None, alias="X-Ohm-Session"),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Accept SSO session header, or enterprise API key bound to an org."""
    st = _state()
    if x_ohm_session:
        session = await st.sso.resolve_session(x_ohm_session)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired SSO session")
        org = await st.orgs.get(session.org_id)
        if not org or org.status != "active":
            raise HTTPException(status_code=403, detail="Org inactive")
        return {
            "mode": "sso",
            "org": org,
            "email": session.email,
            "role": session.role,
            "tenant": None,
        }
    key, tenant = await auth_tenant(authorization)
    if not tenant.org_id:
        raise HTTPException(
            status_code=400,
            detail="API key is not bound to an org — create/join an org first",
        )
    org = await st.orgs.get(tenant.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    return {
        "mode": "api_key",
        "org": org,
        "email": "",
        "role": "service",
        "tenant": tenant,
        "api_key": key,
    }


class CreateOrgBody(BaseModel):
    name: str
    owner_email: str
    plan: str = "payg"
    sso_domain: str = ""
    terms_ack: bool = False
    dpa_ack: bool = False


class CostCentersBody(BaseModel):
    cost_centers: list[str] = Field(default_factory=list)


class PolicyBody(BaseModel):
    allowed_purposes: list[str] | None = None
    model_allowlist: list[str] | None = None
    fetch_cap_day: int | None = None
    default_cache_no_store: bool | None = None
    managed_keys: bool | None = None


class MintKeyBody(BaseModel):
    cost_center: str = "default"
    label: str = ""
    plan: str = ""


class DevSsoBody(BaseModel):
    email: str
    org_id: str
    secret: str


class MemberBody(BaseModel):
    email: str
    role: str = "member"


@router.post("/v1/org")
async def create_org(
    body: CreateOrgBody,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Create an org and bind the caller's tenant key to it."""
    st = _state()
    _key, tenant = auth
    if not body.terms_ack or not body.dpa_ack:
        raise HTTPException(status_code=400, detail="terms_ack and dpa_ack required")
    plan = body.plan if body.plan in ("payg", "enterprise") else tenant.plan
    if plan == "enterprise" and tenant.plan not in ("enterprise", "dev"):
        # Allow enterprise org create only for enterprise/dev seats (or admin later).
        plan = "payg"
    org = await st.orgs.create(
        name=body.name,
        owner_email=body.owner_email,
        plan=plan if plan in ("payg", "enterprise") else "payg",
        sso_domain=body.sso_domain,
        terms_version=st.settings.at_compliance_terms_version,
        dpa_version=st.settings.at_compliance_dpa_version,
    )
    await st.tenants.attach_org(tenant.tenant_id, org.org_id, seed=tenant)
    await st.audit.record(
        org_id=org.org_id,
        tenant_id=tenant.tenant_id,
        actor=body.owner_email,
        action="org.create",
        detail={"name": org.name, "plan": org.plan},
    )
    return {"org": st.orgs.public_view(org), "bound_tenant": tenant.tenant_id}


@router.get("/v1/org")
async def get_org(ctx: dict[str, Any] = Depends(auth_org_session)) -> dict[str, Any]:
    st = _state()
    return {"org": st.orgs.public_view(ctx["org"]), "actor": ctx.get("email"), "role": ctx.get("role")}


@router.put("/v1/org/cost-centers")
async def set_cost_centers(
    body: CostCentersBody,
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    st = _state()
    if ctx.get("role") not in ("owner", "admin", "service"):
        raise HTTPException(status_code=403, detail="admin role required")
    org = await st.orgs.set_cost_centers(ctx["org"].org_id, body.cost_centers)
    await st.audit.record(
        org_id=org.org_id,
        actor=ctx.get("email") or "api_key",
        action="org.cost_centers",
        detail={"cost_centers": org.cost_centers},
    )
    return {"org": st.orgs.public_view(org)}


@router.put("/v1/org/policy")
async def set_policy(
    body: PolicyBody,
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    st = _state()
    if ctx.get("role") not in ("owner", "admin", "service"):
        raise HTTPException(status_code=403, detail="admin role required")
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    org = await st.orgs.update_policy(ctx["org"].org_id, patch)
    await st.audit.record(
        org_id=org.org_id,
        actor=ctx.get("email") or "api_key",
        action="org.policy",
        detail=patch,
    )
    return {"org": st.orgs.public_view(org)}


@router.post("/v1/org/members")
async def add_member(
    body: MemberBody,
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    st = _state()
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="admin role required")
    org = await st.orgs.add_member(ctx["org"].org_id, body.email, body.role)
    await st.audit.record(
        org_id=org.org_id,
        actor=ctx.get("email") or "",
        action="org.member_add",
        detail={"email": body.email, "role": body.role},
    )
    return {"org": st.orgs.public_view(org)}


@router.post("/v1/org/keys")
async def mint_org_key(
    body: MintKeyBody,
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    """Mint a service API key bound to this org + cost center."""
    st = _state()
    if ctx.get("role") not in ("owner", "admin", "service"):
        raise HTTPException(status_code=403, detail="admin role required")
    org = ctx["org"]
    centers = org.cost_centers or ["default"]
    cc = body.cost_center if body.cost_center in centers else centers[0]
    plan = body.plan if body.plan in ("payg", "enterprise", "dev") else org.plan
    raw_key, record = await st.tenants.issue(
        plan=plan,
        label=body.label or f"{org.name}-{cc}",
        terms_version=org.terms_version or st.settings.at_compliance_terms_version,
        dpa_version=org.dpa_version or st.settings.at_compliance_dpa_version,
        org_id=org.org_id,
        cost_center=cc,
    )
    await st.audit.record(
        org_id=org.org_id,
        tenant_id=record.tenant_id,
        actor=ctx.get("email") or "api_key",
        action="org.key_mint",
        detail={"cost_center": cc, "key_prefix": record.key_prefix},
    )
    return {
        "api_key": raw_key,
        "tenant": await st.tenants.public_view(record),
        "note": "Store the api_key now — it cannot be retrieved again.",
    }


@router.get("/v1/org/ledger")
async def org_ledger(
    cost_center: str = "",
    limit: int = Query(default=200, ge=1, le=5000),
    since_ts: int = 0,
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    st = _state()
    org = ctx["org"]
    summary = await st.ledger.summarize(
        org_id=org.org_id, cost_center=cost_center, since_ts=since_ts
    )
    events = await st.ledger.list_events(
        org_id=org.org_id,
        cost_center=cost_center,
        limit=limit,
        since_ts=since_ts,
    )
    return {
        "org_id": org.org_id,
        "summary": summary,
        "events": st.ledger.export_json(events),
    }


@router.get("/v1/org/ledger/export")
async def org_ledger_export(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    cost_center: str = "",
    since_ts: int = 0,
    until_ts: int = 0,
    month: str = "",
    ctx: dict[str, Any] = Depends(auth_org_session),
):
    st = _state()
    org = ctx["org"]
    if month:
        since_ts, until_ts = month_utc_bounds(month)
    events = await st.ledger.list_events(
        org_id=org.org_id,
        cost_center=cost_center,
        limit=10_000,
        since_ts=since_ts,
        until_ts=until_ts,
    )
    await st.audit.record(
        org_id=org.org_id,
        actor=ctx.get("email") or "api_key",
        action="org.ledger_export",
        detail={"format": format, "count": len(events), "month": month or None},
    )
    if format == "json":
        return {
            "org_id": org.org_id,
            "exported_at": int(time.time()),
            "month": month or None,
            "since_ts": since_ts or None,
            "until_ts": until_ts or None,
            "events": st.ledger.export_json(events),
            "summary": await st.ledger.summarize(
                org_id=org.org_id,
                cost_center=cost_center,
                since_ts=since_ts,
                until_ts=until_ts,
            ),
        }
    csv_body = st.ledger.export_csv(events)
    fname = (
        f"ohm-ledger-{org.org_id}-{month}.csv"
        if month
        else f"ohm-ledger-{org.org_id}.csv"
    )
    return PlainTextResponse(
        csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/v1/org/ledger/statement")
async def org_ledger_statement(
    month: str = Query(..., description="UTC calendar month YYYY-MM"),
    cost_center: str = "",
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    """Monthly FinOps statement — summary by cost center for a UTC month."""
    st = _state()
    org = ctx["org"]
    since_ts, until_ts = month_utc_bounds(month)
    summary = await st.ledger.summarize(
        org_id=org.org_id,
        cost_center=cost_center,
        since_ts=since_ts,
        until_ts=until_ts,
    )
    await st.audit.record(
        org_id=org.org_id,
        actor=ctx.get("email") or "api_key",
        action="org.ledger_statement",
        detail={"month": month, "event_count": summary.get("event_count", 0)},
    )
    return {
        "org_id": org.org_id,
        "month": month,
        "since_ts": since_ts,
        "until_ts": until_ts,
        "timezone": "UTC",
        "summary": summary,
        "by_cost_center": summary.get("by_cost_center", {}),
        "pipe_rent_usd": summary.get("pipe_rent_usd", 0),
        "estimated_provider_avoided_usd": summary.get(
            "estimated_provider_avoided_usd", 0
        ),
        "cache_hits": summary.get("cache_hits", 0),
        "cache_misses": summary.get("cache_misses", 0),
        "fetches": summary.get("fetches", 0),
        "estimate_only": True,
        "note": (
            "FinOps export contract: pipe rent is billable Ohm meters; "
            "estimated_provider_avoided_usd is blended list estimate on cache "
            "hits only. Provider invoice import / true reconcile not yet wired."
        ),
    }


@router.get("/v1/org/audit")
async def org_audit(
    limit: int = Query(default=100, ge=1, le=1000),
    ctx: dict[str, Any] = Depends(auth_org_session),
) -> dict[str, Any]:
    st = _state()
    org = ctx["org"]
    if not org.audit_logs and org.plan != "enterprise":
        raise HTTPException(status_code=403, detail="Audit logs require enterprise plan")
    entries = await st.audit.list_entries(org_id=org.org_id, limit=limit)
    return {
        "org_id": org.org_id,
        "entries": [
            {
                "audit_id": e.audit_id,
                "ts": e.ts,
                "actor": e.actor,
                "action": e.action,
                "allowed": e.allowed,
                "detail": e.detail,
            }
            for e in entries
        ],
    }


@router.get("/v1/org/sso/status")
async def sso_status() -> dict[str, Any]:
    st = _state()
    return {
        "oidc_configured": bool(
            st.settings.at_oidc_issuer and st.settings.at_oidc_client_id
        ),
        "dev_sso_available": bool(st.settings.at_sso_dev_secret),
        "authorize_ready": st.sso.configured(),
        "redirect_uri": st.settings.at_oidc_redirect_uri,
    }


@router.get("/v1/org/sso/authorize")
async def sso_authorize(state_param: str = Query(default="", alias="state")) -> dict[str, Any]:
    st = _state()
    if not st.settings.at_oidc_issuer:
        raise HTTPException(
            status_code=501,
            detail="OIDC not configured — use POST /v1/org/sso/dev-login for local",
        )
    st_token = state_param or secrets.token_urlsafe(16)
    url = st.sso.authorize_url(
        state=st_token, redirect_uri=st.settings.at_oidc_redirect_uri
    )
    return {"authorize_url": url, "state": st_token}


@router.post("/v1/org/sso/dev-login")
async def sso_dev_login(body: DevSsoBody) -> dict[str, Any]:
    st = _state()
    try:
        session = await st.sso.dev_login(
            email=body.email, org_id=body.org_id, secret=body.secret
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await st.audit.record(
        org_id=body.org_id,
        actor=body.email,
        action="sso.dev_login",
        detail={},
    )
    return {
        "session_token": session.token,
        "org_id": session.org_id,
        "email": session.email,
        "role": session.role,
        "expires_at": session.expires_at,
        "header": "X-Ohm-Session",
    }


class OidcCallbackBody(BaseModel):
    code: str
    org_id: str = ""
    email_domain_org: bool = True


@router.post("/v1/org/sso/callback")
async def sso_callback(body: OidcCallbackBody) -> dict[str, Any]:
    st = _state()
    try:
        claims = await st.sso.exchange_code(
            code=body.code, redirect_uri=st.settings.at_oidc_redirect_uri
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"OIDC exchange failed: {exc}") from exc
    email = claims["email"]
    domain = email.split("@")[-1] if "@" in email else ""
    org = None
    if body.org_id:
        org = await st.orgs.get(body.org_id)
    elif domain:
        org = await st.orgs.get_by_domain(domain)
    if not org:
        raise HTTPException(
            status_code=404,
            detail="No org for this identity — create an org or set sso_domain",
        )
    role = org.members.get(email, "member")
    if email not in org.members:
        await st.orgs.add_member(org.org_id, email, "member")
        role = "member"
    session = await st.sso.mint_session(org_id=org.org_id, email=email, role=role)
    await st.audit.record(
        org_id=org.org_id, actor=email, action="sso.login", detail={"domain": domain}
    )
    return {
        "session_token": session.token,
        "org_id": org.org_id,
        "email": email,
        "role": role,
        "expires_at": session.expires_at,
        "header": "X-Ohm-Session",
    }


# --- Minimal SCIM 2.0 Users (enterprise-gated) ---------------------------------

@router.get("/v1/scim/v2/Users")
async def scim_list_users(
    authorization: str | None = Header(default=None),
    filter: str = "",
) -> dict[str, Any]:
    st = _state()
    _key, tenant = await auth_tenant(authorization)
    if tenant.plan != "enterprise" or not tenant.org_id:
        raise HTTPException(status_code=403, detail="SCIM requires enterprise org key")
    org = await st.orgs.get(tenant.org_id)
    if not org or not org.scim_enabled:
        raise HTTPException(status_code=403, detail="SCIM not enabled for org")
    resources = []
    for email, role in org.members.items():
        if filter and email not in filter:
            continue
        resources.append(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": email,
                "userName": email,
                "active": True,
                "emails": [{"value": email, "primary": True}],
                "roles": [{"value": role}],
            }
        )
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "Resources": resources,
    }


class ScimUserBody(BaseModel):
    userName: str = ""
    active: bool = True
    emails: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/v1/scim/v2/Users")
async def scim_create_user(
    body: ScimUserBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    st = _state()
    _key, tenant = await auth_tenant(authorization)
    if tenant.plan != "enterprise" or not tenant.org_id:
        raise HTTPException(status_code=403, detail="SCIM requires enterprise org key")
    org = await st.orgs.get(tenant.org_id)
    if not org or not org.scim_enabled:
        raise HTTPException(status_code=403, detail="SCIM not enabled")
    email = (body.userName or "").lower()
    if not email and body.emails:
        email = str(body.emails[0].get("value") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="userName required")
    await st.orgs.add_member(org.org_id, email, "member")
    await st.audit.record(
        org_id=org.org_id,
        actor="scim",
        action="scim.user_create",
        detail={"email": email},
    )
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": email,
        "userName": email,
        "active": body.active,
    }
