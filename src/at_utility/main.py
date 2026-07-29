"""FastAPI OpenAI-compatible gateway."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from at_utility.auth import extract_bearer
from at_utility.cache import cache_key_for_request
from at_utility.compliance.policy import ALLOWED_PURPOSES, BLOCKED_PURPOSES, PURPOSE_RISK
from at_utility.compliance.terms import assert_cache_training_denied, terms_metadata
from at_utility.config import Settings, get_settings
from at_utility.ingest import fetch_web_context, inject_context_messages
from at_utility.metering import Meter
from at_utility.providers import (
    AnthropicProvider,
    MockProvider,
    OpenAIProvider,
    ProviderUpstreamError,
    model_needs_upstream,
    provider_key_available,
    resolve_provider,
)
from at_utility.redis_store import CacheStore, build_store, tenant_key
from at_utility.stream_usage import approx_tokens_from_sse_lines, usage_from_sse_line
from at_utility import stripe_billing
from at_utility.tenants import TenantRecord, TenantRegistry

log = logging.getLogger("at_utility")
logging.basicConfig(level=logging.INFO)


class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatCompletionRequest(BaseModel):
    model: str = "mock"
    messages: list[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    fetch_web_context: bool = False
    web_query: Optional[str] = None
    web_urls: list[str] = Field(default_factory=list)
    # Legal gates — required when fetch_web_context=true (see docs/LEGAL.md)
    web_purpose: Optional[str] = None
    web_compliance_ack: bool = False
    terms_ack: bool = False
    dpa_ack: bool = False
    # markdown (default) | json — structured scrape via ingest worker
    web_format: Optional[str] = None
    # identical-request-replay | no_store (skip Redis write)
    cache_control: Optional[str] = None


class AppState:
    settings: Settings
    store: CacheStore
    meter: Meter
    tenants: TenantRegistry
    mock: MockProvider
    openai: Optional[OpenAIProvider]
    anthropic: Optional[AnthropicProvider]


state = AppState()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    store = await build_store(settings)
    state.settings = settings
    state.store = store
    state.meter = Meter(store, settings)
    state.tenants = TenantRegistry(store, settings)
    state.mock = MockProvider()
    # Always construct shells so BYOK can clone with X-Ohm-Upstream-Key
    state.openai = OpenAIProvider(
        settings.openai_api_key or "", settings.openai_base_url
    )
    state.anthropic = AnthropicProvider(settings.anthropic_api_key or "")
    log.info("ohm gateway ready region=%s", settings.at_region)
    yield
    await store.close()


def _expose_openapi(settings: Settings) -> bool:
    """OpenAPI UI only on local/dev regions — not on public edges."""
    return settings.at_region in {"local", "dev", "test"}


_boot = get_settings()
app = FastAPI(
    title="Ohm",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _expose_openapi(_boot) else None,
    redoc_url="/redoc" if _expose_openapi(_boot) else None,
    openapi_url="/openapi.json" if _expose_openapi(_boot) else None,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)


def _openai_error(
    *,
    message: str,
    status_code: int,
    err_type: str = "invalid_request_error",
    code: str | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "message": message,
            "type": err_type,
            "code": code,
            "param": None,
        }
    }
    if extra:
        body["error"].update(extra)
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("code") or detail)
        code = detail.get("code") if isinstance(detail.get("code"), str) else None
        return _openai_error(
            message=message,
            status_code=exc.status_code,
            code=code,
            extra={"details": detail} if detail else None,
        )
    return _openai_error(message=str(detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _openai_error(
        message="Invalid request",
        status_code=422,
        code="validation_error",
        extra={"details": exc.errors()},
    )


async def auth_tenant(
    authorization: str | None = Header(default=None),
) -> tuple[str, TenantRecord]:
    key = extract_bearer(authorization)
    record = await state.tenants.resolve(key)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if record.is_expired():
        raise HTTPException(
            status_code=403,
            detail="Tenant expired — renew design-partner window or upgrade billing",
        )
    # Hard cutover after dunning window (default 14 days past first payment_failed)
    if (
        record.billing_delinquent_since
        and record.status == "active"
        and state.settings.at_delinquent_suspend_days > 0
    ):
        age_days = (int(time.time()) - record.billing_delinquent_since) / 86400.0
        if age_days >= state.settings.at_delinquent_suspend_days:
            updated = await state.tenants.set_status(record.tenant_id, "suspended")
            if updated:
                record = updated
    if record.status != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "Tenant suspended — update billing at withohm.dev/billing/intermediate "
                "or contact partners@withohm.dev"
            ),
        )
    if record.soft_quota_usd and record.soft_quota_usd > 0:
        snap = await state.meter.snapshot(record.tenant_id)
        revenue = float(snap.get("revenue_usd") or 0)
        if revenue >= record.soft_quota_usd:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Soft usage quota reached ({record.soft_quota_usd} USD estimate). "
                    "Contact partners@withohm.dev or upgrade."
                ),
            )
    return key, record


async def auth_dep(
    authorization: str | None = Header(default=None),
) -> str:
    key, _record = await auth_tenant(authorization)
    return key


async def admin_dep(
    authorization: str | None = Header(default=None),
) -> str:
    key = extract_bearer(authorization)
    if not state.settings.is_admin_api_key(key):
        raise HTTPException(status_code=403, detail="Admin API key required")
    return key


async def rate_limit(api_key: str, tenant_id: str) -> None:
    ok = await state.store.eval_token_bucket(
        tenant_key(tenant_id, "rl", state.settings.at_region),
        state.settings.at_rate_limit_rps,
        state.settings.at_rate_limit_burst,
        time.time(),
    )
    if not ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.get("/health")
async def health() -> dict[str, Any]:
    """Cheap liveness for load balancers / Global Accelerator."""
    return {
        "ok": True,
        "service": "ohm",
        "plane": "python",
        "region": state.settings.at_region,
    }


@app.get("/ready")
async def ready() -> JSONResponse:
    """Readiness: Redis ping + provider configuration flags (not upstream probes)."""
    redis_ok = False
    redis_error: str | None = None
    try:
        pong = await state.store.ping()
        redis_ok = bool(pong)
    except Exception as exc:  # noqa: BLE001 — surface readiness, don't crash
        redis_error = str(exc)
    body = {
        "ok": redis_ok,
        "service": "ohm",
        "plane": "python",
        "region": state.settings.at_region,
        "redis": {"ok": redis_ok, "error": redis_error},
        "providers": {
            "mock": True,
            "openai": bool(state.openai and state.openai._api_key),
            "anthropic": bool(state.anthropic and state.anthropic._api_key),
            "byok_header": "X-Ohm-Upstream-Key",
        },
        "mvp": {
            "public_api_host": "api.withohm.dev",
            "local_edge": "http://localhost:8081/v1",
            "key_prefix": "sk-at",
            "mid_stream_failover": False,
        },
    }
    return JSONResponse(status_code=200 if redis_ok else 503, content=body)


@app.get("/v1/models")
async def list_models(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    return {
        "object": "list",
        "data": [
            {"id": "mock", "object": "model", "owned_by": "ohm"},
            {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
            {"id": "claude-3-5-sonnet-latest", "object": "model", "owned_by": "anthropic"},
        ],
        "byok_header": "X-Ohm-Upstream-Key",
        "note": "Non-mock models require X-Ohm-Upstream-Key (BYOK) unless env/enterprise managed keys are configured.",
    }


@app.get("/v1/usage")
async def usage(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    snap = await state.meter.snapshot(tenant.tenant_id)
    snap["plan"] = tenant.plan
    snap["status"] = tenant.status
    snap["invoice_basis"] = "seat_plus_meters"
    snap["usage_estimate_only"] = False
    snap["billing_model"] = stripe_billing.BILLING_MODEL
    snap["byok"] = True
    snap["billing_paid"] = bool(tenant.billing_paid)
    # Unlock soft fetch cap when paid invoice or any metered spend recorded
    snap["usage_unlocked"] = bool(
        tenant.billing_paid
        or tenant.plan in ("enterprise", "dev", "design_partner")
        or float(snap.get("revenue_usd") or 0) > 0
    )
    return snap


@app.get("/v1/savings")
async def savings_dashboard(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Habit-loop dashboard: money not sent upstream thanks to cache hits."""
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    snap = await state.meter.snapshot(tenant.tenant_id)
    hit_tok = float(snap.get("cache_hit_tokens") or 0)
    miss_price = state.settings.at_price_per_1k_tokens_miss
    # Counterfactual: if hits had been misses at miss price
    avoided_usd = (hit_tok / 1000.0) * miss_price
    return {
        "tenant": tenant.tenant_id,
        "plan": tenant.plan,
        "cache_hit_ratio": snap.get("cache_hit_ratio"),
        "cache_hit_tokens": hit_tok,
        "estimated_upstream_avoided_usd": avoided_usd,
        "billed_hit_usd": snap.get("cache_hit_usd"),
        "billed_miss_usd": snap.get("cache_miss_usd"),
        "revenue_usd": snap.get("revenue_usd"),
        "estimate_only": True,
        "message": (
            "Estimated upstream cost avoided from identical-request cache hits — "
            "not a guaranteed savings promise. Ohm invoice ≠ provider pay-as-you-go."
        ),
    }


@app.get("/v1/enterprise/skus")
async def enterprise_skus(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    s = state.settings
    return {
        "skus": [
            {
                "id": "payg-cache-arbitrage",
                "billing": "seat_plus_meters",
                "billing_model": stripe_billing.BILLING_MODEL,
                "note": (
                    "Stripe charges a monthly seat plus Billing Meters "
                    "(ohm_cache_hit / ohm_cache_miss). Model tokens are BYOK — "
                    "customer pays the provider directly."
                ),
                "price_per_1k_tokens_hit": s.at_price_per_1k_tokens_hit,
                "price_per_1k_tokens_miss": s.at_price_per_1k_tokens_miss,
                "meter_events": {
                    "cache_hit": s.stripe_meter_event_cache_hit,
                    "cache_miss": s.stripe_meter_event_cache_miss,
                },
            },
            {
                "id": "payg-web-fetch",
                "billing": "seat_plus_meters",
                "billing_model": stripe_billing.BILLING_MODEL,
                "note": "Primary variable revenue — compliant URL ingest (Ohm-owned).",
                "price_per_fetch": s.at_price_per_fetch,
                "meter_events": {"web_fetch": s.stripe_meter_event_web_fetch},
            },
            {
                "id": "enterprise-dedicated-pool",
                "billing": "monthly",
                "billing_model": "subscription_seat",
                "price_usd": s.at_enterprise_monthly_usd,
                "managed_keys": True,
                "sla": None,
                "sla_note": "No contractual uptime SLA published for MVP; capacity SKU only.",
                "includes": [
                    "dedicated_connection_pools",
                    "single_tenant_redis",
                    "regional_quota_reservation",
                    "audit_logs",
                    "managed_provider_keys",
                ],
            },
            {
                "id": "design-partner",
                "billing": "complimentary",
                "billing_model": "design_partner",
                "default_days": s.at_design_partner_days,
                "soft_quota_usd": s.at_design_partner_soft_quota_usd,
                "request_cap": s.at_design_partner_request_cap,
            },
        ]
    }


@app.get("/v1/providers")
async def providers_status(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Non-secret provider readiness (key present / not validated against upstream)."""
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    return {
        "providers": {
            "mock": {"configured": True, "ready": True},
            "openai": {
                "configured": bool(state.settings.openai_api_key),
                "ready": bool(state.openai),
                "base_url": state.settings.openai_base_url,
                "byok": True,
            },
            "anthropic": {
                "configured": bool(state.settings.anthropic_api_key),
                "ready": bool(state.anthropic),
                "byok": True,
            },
        },
        "byok_header": "X-Ohm-Upstream-Key",
        "billing_model": stripe_billing.BILLING_MODEL,
    }


@app.get("/v1/compliance/policy")
async def compliance_policy(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Public operating bounds for web ingestion + adjacent frameworks."""
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    s = state.settings
    assert_cache_training_denied(s.at_compliance_allow_cache_training)
    return {
        "enforce": s.at_compliance_enforce,
        "jurisdiction_profile": s.at_compliance_jurisdiction,
        "respect_robots": s.at_compliance_respect_robots,
        "redact_pii": s.at_compliance_redact_pii,
        "require_ack": s.at_compliance_require_ack,
        "require_terms_ack": s.at_compliance_require_terms_ack,
        "max_chars_per_source": s.at_compliance_max_chars_per_source,
        "max_context_chars": s.at_compliance_max_context_chars,
        "allow_cache_training": s.at_compliance_allow_cache_training,
        "cache_purpose": "identical-request-replay",
        "allowed_purposes": sorted(ALLOWED_PURPOSES),
        "blocked_purposes": sorted(BLOCKED_PURPOSES),
        "risk_bands": PURPOSE_RISK,
        "terms": terms_metadata(
            terms_version=s.at_compliance_terms_version,
            dpa_version=s.at_compliance_dpa_version,
            require_terms_ack=s.at_compliance_require_terms_ack,
        ),
        "adjacent_frameworks": [
            "customer_terms_dpa",
            "upstream_provider_tos",
            "copyright_excerpt_caps",
            "uk_pecr_anti_spam",
            "eu_gdpr_readiness",
            "consumer_billing_hygiene",
        ],
        "rules": [
            "Public http(s) pages only — no login, credentials, tokens, or private hosts",
            "No lead harvesting, person dossiers, biometrics, or PECR cold outreach lists",
            "Short excerpts only — copyright / database-right minimisation",
            "Cache is identical-request replay only — never a training corpus",
            "UK: public identifiable data remains personal data; outputs are minimised",
            "US: CFAA/CCPA — public retrieval ≠ authorization to bypass gates",
            "robots.txt respected by default; cite sources; no private-fact invention",
        ],
        "docs": "docs/LEGAL.md",
        "tenant_terms_version": getattr(tenant, "terms_version", "") or None,
        "tenant_dpa_version": getattr(tenant, "dpa_version", "") or None,
    }


class IssueTenantBody(BaseModel):
    plan: str = "payg"
    label: str = ""
    terms_ack: bool = False
    dpa_ack: bool = False
    expires_at: int = 0
    soft_quota_usd: float = 0.0
    request_cap: int = 0
    partner_days: int = 0


class TenantStatusBody(BaseModel):
    status: str


class CheckoutBody(BaseModel):
    plan: str = "payg"
    success_url: str = ""
    cancel_url: str = ""


class PublicCheckoutBody(BaseModel):
    plan: str = "payg"
    label: str = ""
    email: str = ""
    terms_ack: bool = False
    dpa_ack: bool = False
    success_url: str = ""
    cancel_url: str = ""


@app.post("/v1/billing/checkout")
async def public_create_checkout(body: PublicCheckoutBody) -> dict[str, Any]:
    """
    Self-serve: issue Ohm tenant key once + Stripe Checkout URL.
    Admin checkout remains an ops escape hatch.
    """
    s = state.settings
    if body.plan not in ("payg", "enterprise"):
        raise HTTPException(status_code=400, detail="plan must be payg or enterprise")
    if s.at_compliance_enforce and s.at_compliance_require_terms_ack:
        if not body.terms_ack or not body.dpa_ack:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "terms_ack_required",
                    "message": "Checkout requires terms_ack and dpa_ack true "
                    f"(versions {s.at_compliance_terms_version} / {s.at_compliance_dpa_version})",
                },
            )
    if not stripe_billing.stripe_configured(s):
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured (set STRIPE_SECRET_KEY and price IDs)",
        )
    raw_key, record = await state.tenants.issue(
        plan=body.plan,
        label=body.label or body.email or "self-serve",
        terms_version=s.at_compliance_terms_version if body.terms_ack else "",
        dpa_version=s.at_compliance_dpa_version if body.dpa_ack else "",
    )
    try:
        session = stripe_billing.create_checkout_session(
            s,
            tenant_id=record.tenant_id,
            plan=body.plan,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            customer_email=body.email,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "api_key": raw_key,
        "tenant": await state.tenants.public_view(record),
        "checkout": session,
        "note": "Store api_key now; it is not shown again. Complete Checkout to keep the seat active.",
        "byok_header": "X-Ohm-Upstream-Key",
        "billing_model": stripe_billing.BILLING_MODEL,
    }


@app.post("/v1/admin/tenants")
async def admin_issue_tenant(
    body: IssueTenantBody,
    _admin: str = Depends(admin_dep),
) -> dict[str, Any]:
    s = state.settings
    if s.at_compliance_enforce and s.at_compliance_require_terms_ack:
        if not body.terms_ack or not body.dpa_ack:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "terms_ack_required",
                    "message": "Issuing a tenant requires terms_ack and dpa_ack true "
                    f"(versions {s.at_compliance_terms_version} / {s.at_compliance_dpa_version})",
                },
            )
    soft = body.soft_quota_usd
    caps = body.request_cap
    days = body.partner_days
    if body.plan == "design_partner":
        if soft <= 0:
            soft = s.at_design_partner_soft_quota_usd
        if caps <= 0:
            caps = s.at_design_partner_request_cap
        if days <= 0:
            days = s.at_design_partner_days
    raw_key, record = await state.tenants.issue(
        plan=body.plan,
        label=body.label,
        terms_version=s.at_compliance_terms_version if body.terms_ack else "",
        dpa_version=s.at_compliance_dpa_version if body.dpa_ack else "",
        expires_at=body.expires_at,
        soft_quota_usd=soft,
        request_cap=caps,
        partner_days=days or s.at_design_partner_days,
    )
    return {
        "api_key": raw_key,
        "tenant": await state.tenants.public_view(record),
        "note": "Store api_key now; it is not shown again.",
    }


@app.post("/v1/admin/tenants/{tenant_id}/status")
async def admin_set_tenant_status(
    tenant_id: str,
    body: TenantStatusBody,
    _admin: str = Depends(admin_dep),
) -> dict[str, Any]:
    if body.status not in ("active", "suspended"):
        raise HTTPException(status_code=400, detail="status must be active or suspended")
    record = await state.tenants.set_status(tenant_id, body.status)
    if record is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"tenant": await state.tenants.public_view(record)}


@app.post("/v1/admin/tenants/{tenant_id}/checkout")
async def admin_create_checkout(
    tenant_id: str,
    body: CheckoutBody,
    _admin: str = Depends(admin_dep),
) -> dict[str, Any]:
    if not stripe_billing.stripe_configured(state.settings):
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured (set STRIPE_SECRET_KEY and price IDs)",
        )
    try:
        session = stripe_billing.create_checkout_session(
            state.settings,
            tenant_id=tenant_id,
            plan=body.plan,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return session


@app.post("/v1/billing/webhook")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe_billing.construct_webhook_event(
            state.settings, payload, signature
        )
    except Exception as exc:  # noqa: BLE001 — Stripe signature errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    event_type = event["type"] if isinstance(event, dict) else event.type
    data_obj = event["data"]["object"] if isinstance(event, dict) else event.data.object

    def _as_mapping(obj: Any) -> dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "to_dict"):
            try:
                return dict(obj.to_dict())
            except Exception:  # noqa: BLE001
                pass
        out: dict[str, Any] = {}
        for key in (
            "metadata",
            "client_reference_id",
            "customer",
            "subscription",
            "id",
        ):
            try:
                val = obj[key] if hasattr(obj, "__getitem__") else getattr(obj, key, None)
            except Exception:  # noqa: BLE001
                val = getattr(obj, key, None)
            if val is not None:
                out[key] = val
        return out

    obj = _as_mapping(data_obj)
    meta_raw = obj.get("metadata") or {}
    meta = _as_mapping(meta_raw)
    tenant_id = meta.get("tenant_id") or obj.get("client_reference_id")
    customer_id = obj.get("customer") or ""
    subscription_id = obj.get("subscription") or obj.get("id") or ""
    plan = meta.get("plan")
    subscription_status = str(obj.get("status") or "")

    if not tenant_id and customer_id:
        found = await state.tenants.find_by_stripe_customer(str(customer_id))
        if found:
            tenant_id = found.tenant_id
            if not plan:
                plan = found.plan

    new_status = stripe_billing.apply_webhook_to_status(
        event_type, subscription_status=subscription_status
    )
    billing_paid: bool | None = None
    clear_delinquent = False
    delinquent_since: int | None = None

    if event_type == "invoice.paid":
        billing_paid = True
        clear_delinquent = True
    elif event_type == "invoice.payment_failed":
        # Stay active for Smart Retries + reminder emails; lock meters/fetch via flag
        billing_paid = False
        delinquent_since = int(time.time())
    elif event_type in (
        "customer.subscription.deleted",
        "invoice.marked_uncollectible",
    ):
        billing_paid = False
    elif event_type == "customer.subscription.updated":
        st = subscription_status.lower()
        if st in ("canceled", "unpaid", "incomplete_expired"):
            billing_paid = False
        elif st in ("active", "trialing"):
            billing_paid = True
            clear_delinquent = True

    if tenant_id and (
        new_status or billing_paid is not None or delinquent_since or clear_delinquent
    ):
        await state.tenants.attach_stripe(
            tenant_id,
            customer_id=str(customer_id or ""),
            subscription_id=str(subscription_id or ""),
            plan=plan,
            status=new_status,
            billing_paid=billing_paid,
            billing_delinquent_since=delinquent_since,
            clear_delinquent=clear_delinquent,
        )
        log.info(
            "stripe webhook applied tenant=%s status=%s billing_paid=%s "
            "delinquent=%s event=%s sub_status=%s",
            tenant_id,
            new_status,
            billing_paid,
            delinquent_since,
            event_type,
            subscription_status,
        )
    return {"received": True, "type": event_type}


@app.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
    x_ohm_upstream_key: Optional[str] = Header(default=None, alias="X-Ohm-Upstream-Key"),
):
    api_key, tenant_rec = auth
    await rate_limit(api_key, tenant_rec.tenant_id)
    tenant = tenant_rec.tenant_id
    stripe_customer = tenant_rec.stripe_customer_id or ""
    messages = [m.model_dump() for m in body.messages]
    upstream_key = (x_ohm_upstream_key or "").strip()
    # Enterprise managed pool may omit BYOK and use Ohm env keys
    allow_fallback = state.settings.at_byok_allow_env_fallback or (
        tenant_rec.plan in ("enterprise", "dev")
    )

    assert_cache_training_denied(state.settings.at_compliance_allow_cache_training)
    no_store = (body.cache_control or "").strip().lower() == "no_store"

    fetch_count = 0
    web_purpose = body.web_purpose or ""
    if body.fetch_web_context:
        # Soft daily fetch cap until invoice.paid / usage spend unlocks Intermediate.
        # Delinquent tenants (failed invoice in dunning window): hard-block web fetch.
        if tenant_rec.billing_delinquent_since:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "billing_delinquent",
                    "message": (
                        "Web fetch paused while your invoice is past due. "
                        "Update your payment method — Stripe is retrying collection "
                        "and sending reminders. Service suspends after "
                        f"{state.settings.at_delinquent_suspend_days} days unpaid."
                    ),
                },
            )
        cap = int(state.settings.at_free_tier_fetch_cap_day or 0)
        unlocked = (
            tenant_rec.billing_paid
            or tenant_rec.plan in ("enterprise", "dev", "design_partner")
        )
        if not unlocked and float(
            (await state.meter.snapshot(tenant)).get("revenue_usd") or 0
        ) > 0:
            unlocked = True
        if cap > 0 and not unlocked:
            today = await state.meter.today_fetches(tenant)
            # estimate upcoming URLs (best-effort before ingest)
            upcoming = len(body.web_urls or []) or 1
            if today + upcoming > cap:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "fetch_cap_day",
                        "message": (
                            f"Daily web-fetch soft cap ({cap}) reached before "
                            "usage unlock. Complete Checkout so the first paid "
                            "invoice (or metered spend) lifts this cap. "
                            "See /docs/pricing."
                        ),
                        "today_fetches": today,
                        "cap": cap,
                    },
                )
        ctx = await fetch_web_context(
            state.settings,
            query=body.web_query,
            urls=body.web_urls or None,
            purpose=body.web_purpose,
            compliance_ack=body.web_compliance_ack,
            terms_ack=body.terms_ack,
            dpa_ack=body.dpa_ack,
            format=body.web_format or "markdown",
        )
        if ctx.get("ok") is False and ctx.get("error"):
            detail = ctx.get("compliance") or {
                "code": "compliance_denied",
                "message": ctx.get("error"),
            }
            raise HTTPException(status_code=403, detail=detail)
        docs = ctx.get("documents") or []
        markdown = ctx.get("_joined_markdown") or "\n\n".join(
            f"### {d.get('url', 'source')}\n{d.get('markdown', '')}" for d in docs
        )
        web_purpose = (ctx.get("compliance") or {}).get("purpose") or body.web_purpose or (
            "public_web_retrieval"
        )
        if markdown.strip():
            messages = inject_context_messages(
                messages, markdown, purpose=str(web_purpose)
            )
            fetch_count = len([d for d in docs if d.get("ok")]) or 0
            if fetch_count:
                await state.meter.record_fetch(
                    tenant, fetch_count, stripe_customer_id=stripe_customer
                )

    extras = {
        "fetch_web_context": body.fetch_web_context,
        "web_query": body.web_query,
        "web_urls": body.web_urls,
        "web_purpose": body.web_purpose,
        "web_format": body.web_format,
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
        "cache_control": body.cache_control,
    }
    ckey = cache_key_for_request(
        tenant=tenant, model=body.model, messages=messages, extras=extras
    )

    cache_headers = {
        "X-AT-Cache-Purpose": "identical-request-replay",
        "X-AT-Region": state.settings.at_region,
        "X-Ohm-Byok": "1" if upstream_key else "0",
    }

    if not body.stream and not no_store:
        cached = await state.store.get(ckey)
        if cached:
            payload = json.loads(cached)
            usage = payload.get("usage") or {}
            total = int(usage.get("total_tokens") or 0)
            event = await state.meter.record_chat(
                tenant,
                cache_hit=True,
                total_tokens=total,
                stripe_customer_id=stripe_customer,
            )
            return JSONResponse(
                payload,
                headers={
                    **cache_headers,
                    "X-AT-Cache": "HIT",
                    "X-AT-Billed-USD": f"{event.billed_usd:.6f}",
                },
            )

    if model_needs_upstream(body.model) and not provider_key_available(
        body.model,
        upstream_key=upstream_key,
        openai=state.openai,
        anthropic=state.anthropic,
        allow_env_fallback=allow_fallback,
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "upstream_key_required",
                "message": (
                    "BYOK required: send your provider API key as X-Ohm-Upstream-Key "
                    "(Authorization remains your Ohm sk-at-* key). "
                    "Cache hits never need an upstream key."
                ),
                "header": "X-Ohm-Upstream-Key",
            },
        )

    provider, model = resolve_provider(
        body.model,
        openai=state.openai,
        anthropic=state.anthropic,
        mock=state.mock,
        fallback=state.settings.at_fallback_model,
        upstream_key=upstream_key,
        allow_env_fallback=allow_fallback,
    )

    kwargs: dict[str, Any] = {}
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    try:
        if body.stream:
            stream = await provider.chat_completion(
                model=model, messages=messages, stream=True, **kwargs
            )

            async def event_stream() -> AsyncIterator[bytes]:
                collected: list[str] = []
                usage_total: int | None = None
                try:
                    async for line in stream:  # type: ignore[union-attr]
                        text = line if isinstance(line, str) else line.decode("utf-8", errors="replace")
                        collected.append(text)
                        parsed = usage_from_sse_line(text)
                        if parsed is not None:
                            usage_total = parsed
                        yield text.encode("utf-8")
                except ProviderUpstreamError as exc:
                    payload = json.dumps(
                        {
                            "error": {
                                "message": f"{exc.provider} upstream error",
                                "type": "provider_upstream_error",
                                "provider": exc.provider,
                                "upstream": exc.body,
                            }
                        }
                    )
                    yield f"data: {payload}\n\n".encode("utf-8")
                    yield b"data: [DONE]\n\n"
                    return
                total_tokens = (
                    usage_total
                    if usage_total is not None
                    else approx_tokens_from_sse_lines(collected)
                )
                await state.meter.record_chat(
                    tenant,
                    cache_hit=False,
                    total_tokens=total_tokens,
                    stripe_customer_id=stripe_customer,
                )

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    **cache_headers,
                    "X-AT-Cache": "BYPASS" if no_store else "MISS",
                    "Cache-Control": "no-cache",
                },
            )

        result = await provider.chat_completion(
            model=model, messages=messages, stream=False, **kwargs
        )
    except ProviderUpstreamError as exc:
        return JSONResponse(
            {
                "error": {
                    "message": f"{exc.provider} upstream error",
                    "type": "provider_upstream_error",
                    "provider": exc.provider,
                    "upstream": exc.body,
                }
            },
            status_code=exc.status_code if 400 <= exc.status_code < 600 else 502,
            headers={
                **cache_headers,
                "X-AT-Cache": "MISS",
                "X-AT-Provider": exc.provider,
            },
        )

    assert isinstance(result, dict)
    if not no_store:
        await state.store.set(
            ckey, json.dumps(result), ttl_seconds=state.settings.at_cache_ttl_seconds
        )
    usage = result.get("usage") or {}
    total = int(usage.get("total_tokens") or 0)
    event = await state.meter.record_chat(
        tenant,
        cache_hit=False,
        total_tokens=total,
        stripe_customer_id=stripe_customer,
    )
    return JSONResponse(
        result,
        headers={
            **cache_headers,
            "X-AT-Cache": "BYPASS" if no_store else "MISS",
            "X-AT-Billed-USD": f"{event.billed_usd:.6f}",
        },
    )


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "at_utility.main:app",
        host=settings.at_host,
        port=settings.at_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
