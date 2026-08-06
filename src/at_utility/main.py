"""FastAPI OpenAI-compatible gateway."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import time
import urllib.parse
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

import httpx

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from at_utility.auth import extract_bearer
from at_utility.cache import cache_key_for_request
from at_utility import receipts
from at_utility.compliance import web_bot_auth
from at_utility.compliance.policy import ALLOWED_PURPOSES, BLOCKED_PURPOSES, PURPOSE_RISK
from at_utility.compliance.terms import assert_cache_training_denied, terms_metadata
from at_utility.config import Settings, get_settings
from at_utility.ingest import fetch_web_context, inject_context_messages
from at_utility.metering import Meter, STRIPE_METER_DLQ_KEY
from at_utility.providers import (
    OPENAI_COMPAT_VENDORS,
    AnthropicProvider,
    MockProvider,
    OpenAIProvider,
    ProviderUpstreamError,
    build_compat_shells,
    model_needs_upstream,
    provider_key_available,
    resolve_provider,
)
from at_utility.redis_store import CacheStore, build_store, tenant_key
from at_utility.stream_usage import (
    approx_tokens_from_sse_lines,
    assemble_completion_from_sse_lines,
    sse_lines_from_completion,
    usage_from_sse_line,
)
from at_utility import stripe_billing
from at_utility.audit import AuditLog
from at_utility.ledger import CleanLedger, normalize_path
from at_utility.org_api import month_utc_bounds, router as org_router
from at_utility.orgs import OrgRegistry
from at_utility.savings import SAVINGS_DISCLAIMER, dual_ledger
from at_utility.sso import SsoService
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
    # Frequency-farm path label (also accept X-Ohm-Path header)
    ohm_path: Optional[str] = None


class AppState:
    settings: Settings
    store: CacheStore
    meter: Meter
    tenants: TenantRegistry
    orgs: OrgRegistry
    ledger: CleanLedger
    audit: AuditLog
    sso: SsoService
    mock: MockProvider
    openai: Optional[OpenAIProvider]
    anthropic: Optional[AnthropicProvider]
    # OpenAI-compatible vendor shells (gemini/deepseek/moonshot/zai/qwen/xai)
    compat: dict[str, OpenAIProvider]


state = AppState()


def bind_runtime(
    st: AppState,
    store: CacheStore,
    settings: Settings,
    *,
    mock: Optional[MockProvider] = None,
    openai: Optional[OpenAIProvider] = None,
    anthropic: Optional[AnthropicProvider] = None,
    build_provider_shells: bool = False,
) -> None:
    """Wire full AppState (tenants + org/ledger/SSO stack). Safe to call from tests."""
    st.settings = settings
    st.store = store
    st.meter = Meter(store, settings)
    st.tenants = TenantRegistry(store, settings)
    st.orgs = OrgRegistry(store)
    st.ledger = CleanLedger(store, settings)
    st.audit = AuditLog(store)
    st.sso = SsoService(store, settings, st.orgs)
    st.mock = mock if mock is not None else MockProvider()
    if build_provider_shells:
        st.openai = OpenAIProvider(
            settings.openai_api_key or "", settings.openai_base_url
        )
        st.anthropic = AnthropicProvider(settings.anthropic_api_key or "")
    else:
        st.openai = openai
        st.anthropic = anthropic
    # OpenAI-compatible vendor shells (gemini/deepseek/moonshot/zai/qwen/xai)
    st.compat = build_compat_shells(settings)


BILLING_MAINTENANCE_INTERVAL_SECONDS = 60
# Delinquency sweep scans the tenant keyspace — run every Nth tick, not every minute.
DELINQUENCY_SWEEP_EVERY_TICKS = 10


async def _billing_maintenance_loop() -> None:
    """Replay dead-lettered Stripe meter events and enforce dunning deadlines.

    Without this loop, failed meter events are lost (underbilling) and
    delinquent tenants only suspend when they happen to send a request.
    """
    tick = 0
    while True:
        try:
            await state.meter.replay_stripe_dlq()
            if tick % DELINQUENCY_SWEEP_EVERY_TICKS == 0:
                suspended = await state.tenants.sweep_delinquent(
                    state.settings.at_delinquent_suspend_days
                )
                if suspended:
                    log.info("delinquency sweep suspended %d tenants", suspended)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — keep the loop alive
            log.exception("billing maintenance tick failed")
        tick += 1
        await asyncio.sleep(BILLING_MAINTENANCE_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    store = await build_store(settings)
    # Always construct provider shells so BYOK can clone with X-Ohm-Upstream-Key
    bind_runtime(state, store, settings, build_provider_shells=True)
    maintenance = asyncio.create_task(_billing_maintenance_loop())
    log.info("ohm gateway ready region=%s", settings.at_region)
    yield
    maintenance.cancel()
    try:
        await maintenance
    except asyncio.CancelledError:
        pass
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
# Browser Shell / org console (withohm.dev → api). Last added = outermost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.withohm.dev",
        "https://withohm.dev",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https://.*\.amplifyapp\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Ohm-Upstream-Key",
        "X-Ohm-Session",
        "X-Ohm-Path",
        "X-Ohm-Cost-Center",
    ],
    expose_headers=[
        "X-AT-Cache",
        "X-AT-Billed-Usd",
        "X-AT-Plane",
        "X-Ohm-Cost-Center",
        "X-Ohm-Path",
        "X-Ohm-Spend-Cap",
        "X-Ohm-Spend-Cap-Usd",
    ],
    max_age=86400,
)
app.include_router(org_router)


async def _append_ledger(
    tenant_rec: TenantRecord,
    *,
    kind: str,
    model: str = "",
    tokens: int = 0,
    fetches: int = 0,
    pipe_usd: float = 0.0,
    cache_hit: bool = False,
    purpose: str = "",
    request_id: str = "",
    path: str = "default",
) -> None:
    try:
        await state.ledger.append(
            tenant_id=tenant_rec.tenant_id,
            org_id=tenant_rec.org_id or "",
            cost_center=tenant_rec.cost_center or "default",
            kind=kind,
            model=model,
            tokens=tokens,
            fetches=fetches,
            pipe_usd=pipe_usd,
            cache_hit=cache_hit,
            purpose=purpose,
            request_id=request_id,
            path=path,
        )
    except Exception:  # noqa: BLE001 — metering must not fail the request
        log.exception("ledger append failed tenant=%s", tenant_rec.tenant_id)


async def _spend_cap_on_miss(
    tenant_rec: TenantRecord,
) -> dict[str, str]:
    """Before upstream on cache MISS: soft-header or hard-block org spend caps.

    HITs are never gated — they are the arbitrage. Returns extra response headers.
    """
    if not tenant_rec.org_id:
        return {}
    org = await state.orgs.get(tenant_rec.org_id)
    if not org:
        return {}
    policy = org.policy_obj()
    center = (tenant_rec.cost_center or "default").strip() or "default"
    cap = policy.spend_caps_by_cost_center.get(center)
    if cap is None:
        cap = policy.spend_cap_usd_month
    try:
        cap_f = float(cap or 0)
    except (TypeError, ValueError):
        return {}
    if cap_f <= 0:
        return {}
    month = time.strftime("%Y-%m", time.gmtime())
    since_ts, until_ts = month_utc_bounds(month)
    summary = await state.ledger.summarize(
        org_id=org.org_id,
        cost_center=center,
        since_ts=since_ts,
        until_ts=until_ts,
    )
    spent = float(summary.get("pipe_rent_usd") or 0)
    if spent < cap_f:
        return {}
    if policy.spend_cap_mode == "hard":
        await state.audit.record(
            org_id=org.org_id,
            actor=tenant_rec.tenant_id,
            action="org.spend_cap_hard",
            detail={
                "cost_center": center,
                "cap_usd": cap_f,
                "spent_usd": spent,
                "month": month,
            },
        )
        raise HTTPException(
            status_code=402,
            detail={
                "code": "spend_cap_exceeded",
                "message": (
                    f"Org spend cap ${cap_f:.2f} exceeded for cost center "
                    f"'{center}' this UTC month (pipe rent ${spent:.4f}). "
                    "Cache HITs still serve; raise the cap or wait for next month."
                ),
                "cost_center": center,
                "cap_usd": cap_f,
                "spent_usd": spent,
                "month": month,
            },
        )
    await state.audit.record(
        org_id=org.org_id,
        actor=tenant_rec.tenant_id,
        action="org.spend_cap_soft",
        detail={
            "cost_center": center,
            "cap_usd": cap_f,
            "spent_usd": spent,
            "month": month,
        },
    )
    return {
        "X-Ohm-Spend-Cap": "soft",
        "X-Ohm-Spend-Cap-Usd": f"{cap_f:.2f}",
    }


async def _org_policy_gate(tenant_rec: TenantRecord, body: ChatCompletionRequest) -> None:
    """Enforce org model allowlist + purpose allowlist when tenant is org-bound."""
    if not tenant_rec.org_id:
        return
    org = await state.orgs.get(tenant_rec.org_id)
    if not org:
        return
    policy = org.policy_obj()
    if policy.model_allowlist:
        if body.model not in policy.model_allowlist and body.model != "mock":
            await state.audit.record(
                org_id=org.org_id,
                tenant_id=tenant_rec.tenant_id,
                action="policy.model_deny",
                detail={"model": body.model},
                allowed=False,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "model_not_allowlisted",
                    "message": f"Model {body.model} not in org allowlist",
                    "allowlist": policy.model_allowlist,
                },
            )
    if body.fetch_web_context and body.web_purpose:
        if body.web_purpose not in policy.allowed_purposes:
            await state.audit.record(
                org_id=org.org_id,
                tenant_id=tenant_rec.tenant_id,
                action="policy.purpose_deny",
                detail={"purpose": body.web_purpose},
                allowed=False,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "purpose_not_allowed",
                    "message": f"Purpose {body.web_purpose} not allowed by org policy",
                    "allowed_purposes": policy.allowed_purposes,
                },
            )


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


async def _ensure_state() -> None:
    """Idempotent init for ASGI servers/tests that hit routes before lifespan.

    Also hydrates the org/ledger stack when older test fixtures only wired
    tenants — otherwise org routes see AppState without ``orgs``.
    """
    if getattr(state, "tenants", None) is None:
        settings = get_settings()
        store = await build_store(settings)
        bind_runtime(state, store, settings, build_provider_shells=True)
        return
    if getattr(state, "orgs", None) is None:
        store = state.store
        settings = state.settings
        state.orgs = OrgRegistry(store)
        state.ledger = CleanLedger(store, settings)
        state.audit = AuditLog(store)
        state.sso = SsoService(store, settings, state.orgs)


async def auth_tenant(
    authorization: str | None = Header(default=None),
) -> tuple[str, TenantRecord]:
    await _ensure_state()
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
                "Tenant suspended — update billing at https://www.withohm.dev/billing/intermediate "
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
    if record.request_cap and record.request_cap > 0:
        snap = await state.meter.snapshot(record.tenant_id)
        used = int(float(snap.get("requests") or 0))
        if used >= record.request_cap:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "request_cap",
                    "message": (
                        f"Request cap reached ({record.request_cap}). "
                        "Contact partners@withohm.dev to raise the cap."
                    ),
                    "used": used,
                    "cap": record.request_cap,
                },
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


@app.get("/.well-known/http-message-signatures-directory")
async def http_message_signatures_directory(request: Request) -> Response:
    """Public Ed25519 JWKS: OhmBot's Web Bot Auth key + the receipt key.

    Origins verifying `Signature-Agent` fetch this to check OhmBot's RFC 9421
    signatures; customers verifying `X-Ohm-Receipt` JWS receipts resolve the
    signing key by its `kid` (RFC 7638 thumbprint) here. The response is
    self-signed (one directory binding per key, tag
    `http-message-signatures-directory`) as required for Cloudflare Verified
    Bots enrollment. Public keys only — unauthenticated by design; 404 when
    no signing seed is configured.
    """
    keys: list[dict[str, str]] = []
    private_keys = []
    bot_key = web_bot_auth.load_signing_key()
    if bot_key is not None:
        keys.append(web_bot_auth.public_jwk(bot_key))
        private_keys.append(bot_key)
    receipt_key = receipts.load_receipt_key()
    if receipt_key is not None:
        receipt_jwk = receipts.receipt_public_jwk()
        if receipt_jwk not in keys:
            keys.append(receipt_jwk)
            private_keys.append(receipt_key)
    if not keys:
        raise HTTPException(status_code=404, detail="no signing keys configured")
    authority = (request.headers.get("host") or request.url.netloc or "").lower()
    return Response(
        content=json.dumps({"keys": keys}),
        media_type="application/http-message-signatures-directory+json",
        headers={
            "Cache-Control": "max-age=3600",
            **web_bot_auth.directory_binding_headers(authority, private_keys),
        },
    )


@app.get("/ready")
async def ready() -> JSONResponse:
    """Readiness: Redis ping. Prod omits exception strings and internal host hints."""
    redis_ok = False
    redis_error: str | None = None
    try:
        pong = await state.store.ping()
        redis_ok = bool(pong)
    except Exception as exc:  # noqa: BLE001 — surface readiness, don't crash
        redis_error = str(exc)
    region = (state.settings.at_region or "").lower()
    is_prod = region not in ("local", "dev", "test", "")
    body: dict[str, Any] = {
        "ok": redis_ok,
        "service": "ohm",
        "plane": "python",
        "region": state.settings.at_region,
        "redis": {"ok": redis_ok},
    }
    if not is_prod:
        body["redis"]["error"] = redis_error
        body["providers"] = {
            "mock": True,
            "openai": bool(state.openai and state.openai._api_key),
            "anthropic": bool(state.anthropic and state.anthropic._api_key),
            **{
                vendor: bool(shell._api_key)
                for vendor, shell in getattr(state, "compat", {}).items()
            },
            "byok_header": "X-Ohm-Upstream-Key",
        }
        body["mvp"] = {
            "public_api_host": "api.withohm.dev",
            "local_edge": "http://localhost:8081/v1",
            "key_prefix": "sk-at",
            "mid_stream_failover": False,
            "pre_first_byte_stream_failover": True,
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
            {"id": "gemini-3.1-pro", "object": "model", "owned_by": "gemini"},
            {"id": "deepseek-v4", "object": "model", "owned_by": "deepseek"},
            {"id": "kimi-k3", "object": "model", "owned_by": "moonshot"},
            {"id": "glm-5.2", "object": "model", "owned_by": "zai"},
            {"id": "qwen3-max", "object": "model", "owned_by": "qwen"},
            {"id": "grok-4", "object": "model", "owned_by": "xai"},
        ],
        "byok_header": "X-Ohm-Upstream-Key",
        "routing": {
            "prefixes": {
                "gpt-/o1/o3": "openai",
                "claude": "anthropic",
                **{
                    "/".join(prefixes): vendor
                    for vendor, prefixes, _base in OPENAI_COMPAT_VENDORS
                },
            },
            "note": "Model ids are illustrative; any id under a routed prefix is forwarded verbatim to that vendor's OpenAI-compatible endpoint.",
        },
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
    # Soft fetch cap lifts only on a paid invoice (or privileged plan) —
    # metered-but-uninvoiced spend never unlocks.
    snap["usage_unlocked"] = bool(
        tenant.billing_paid
        or tenant.plan in ("enterprise", "dev", "design_partner")
    )
    return snap


@app.get("/v1/savings")
async def savings_dashboard(
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Habit-loop dashboard: dual ledger (provider avoided vs pipe rent)."""
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    snap = await state.meter.snapshot(tenant.tenant_id)
    hit_tok = float(snap.get("cache_hit_tokens") or 0)
    ledger = dual_ledger(
        hit_tokens=hit_tok, snap=snap, settings=state.settings
    )
    return {
        "tenant": tenant.tenant_id,
        "plan": tenant.plan,
        "cache_hit_ratio": snap.get("cache_hit_ratio"),
        "cache_hit_tokens": hit_tok,
        **ledger,
        "billed_hit_usd": snap.get("cache_hit_usd"),
        "billed_miss_usd": snap.get("cache_miss_usd"),
        "revenue_usd": snap.get("revenue_usd"),
        "message": SAVINGS_DISCLAIMER,
        "receipt": {
            "mint": "POST /v1/savings/receipt",
            "note": (
                "Mint a public, shareable savings receipt (page + README badge) "
                "from this snapshot — via the API or the ohm_receipt MCP tool."
            ),
        },
    }


# --- Public savings receipts -------------------------------------------------
# A receipt is an opt-in, immutable snapshot of a tenant's cache savings,
# stored under an unguessable token. The public payload never contains the
# tenant id — only the display name the tenant chose at mint time.

RECEIPT_KEY_PREFIX = "at:global:receipt:"
RECEIPT_TTL_SECONDS = 90 * 86400
RECEIPT_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{8,64}")
PUBLIC_SITE_BASE = "https://www.withohm.dev"
PUBLIC_API_BASE = "https://api.withohm.dev"


def _receipt_links(token: str) -> dict[str, str]:
    badge_endpoint = f"{PUBLIC_API_BASE}/v1/public/receipts/{token}/badge"
    badge_image = (
        "https://img.shields.io/endpoint?url="
        + urllib.parse.quote(badge_endpoint, safe="")
    )
    receipt_url = f"{PUBLIC_SITE_BASE}/r/{token}"
    return {
        "receipt_url": receipt_url,
        "badge_endpoint": badge_endpoint,
        "badge_image_url": badge_image,
        "badge_markdown": f"[![withOhm savings]({badge_image})]({receipt_url})",
    }


def _sanitize_display_name(raw: str) -> str:
    cleaned = "".join(ch for ch in raw if ch.isprintable()).strip()
    return cleaned[:40]


async def _public_rate_limit(request: Request, scope: str) -> None:
    """IP token bucket for unauthenticated public endpoints."""
    client_ip = (
        (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "")
        or "unknown"
    )
    ok = await state.store.eval_token_bucket(
        f"at:global:rl:{scope}:{client_ip}",
        2.0,
        10.0,
        time.time(),
    )
    if not ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


class ReceiptBody(BaseModel):
    display_name: str = ""


@app.post("/v1/savings/receipt")
async def mint_savings_receipt(
    body: ReceiptBody,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Mint a public, shareable savings receipt (immutable snapshot)."""
    api_key, tenant = auth
    await rate_limit(api_key, tenant.tenant_id)
    snap = await state.meter.snapshot(tenant.tenant_id)
    hit_tok = float(snap.get("cache_hit_tokens") or 0)
    ledger = dual_ledger(
        hit_tokens=hit_tok, snap=snap, settings=state.settings
    )
    token = secrets.token_urlsafe(12)
    display = _sanitize_display_name(body.display_name) or "an anonymous workspace"
    receipt = {
        "token": token,
        "display_name": display,
        "created_at": int(time.time()),
        "period": "all-time",
        "cache_hit_tokens": hit_tok,
        "cache_hit_ratio": snap.get("cache_hit_ratio"),
        "requests": snap.get("requests"),
        "estimated_upstream_avoided_usd": ledger["estimated_upstream_avoided_usd"],
        "estimated_provider_avoided_usd": ledger["estimated_provider_avoided_usd"],
        "estimated_pipe_proxy_avoided_usd": ledger[
            "estimated_pipe_proxy_avoided_usd"
        ],
        "pipe_rent_usd": ledger["pipe_rent_usd"],
        "roi_ratio": ledger["roi_ratio"],
        "provider_rate_per_1k_tokens": ledger["provider_rate_per_1k_tokens"],
        "estimate_only": True,
        # Internal only — stripped from the public view. Kept so abuse can be
        # traced back to the minting tenant.
        "_tenant": tenant.tenant_id,
    }
    await state.store.set(
        RECEIPT_KEY_PREFIX + token,
        json.dumps(receipt),
        ttl_seconds=RECEIPT_TTL_SECONDS,
    )
    await state.meter.mark_receipt_minted()
    public = {k: v for k, v in receipt.items() if not k.startswith("_")}
    return {
        "receipt": public,
        **_receipt_links(token),
        "note": (
            "Receipt is public at receipt_url for 90 days. Share it or drop "
            "badge_markdown into a README — estimated savings, not a promise."
        ),
    }


async def _load_public_receipt(token: str) -> dict[str, Any]:
    if not RECEIPT_TOKEN_RE.fullmatch(token or ""):
        raise HTTPException(status_code=404, detail="Receipt not found")
    raw = await state.store.get(RECEIPT_KEY_PREFIX + token)
    if not raw:
        raise HTTPException(status_code=404, detail="Receipt not found")
    receipt = json.loads(raw)
    return {k: v for k, v in receipt.items() if not k.startswith("_")}


@app.get("/v1/public/receipts/{token}")
async def public_receipt(token: str, request: Request) -> dict[str, Any]:
    """Public receipt view — no auth, no tenant data beyond the display name."""
    await _public_rate_limit(request, "receipt")
    receipt = await _load_public_receipt(token)
    return {"receipt": receipt, **_receipt_links(token)}


@app.get("/v1/public/receipts/{token}/badge")
async def public_receipt_badge(token: str, request: Request) -> dict[str, Any]:
    """Shields.io custom-endpoint schema for README badges."""
    await _public_rate_limit(request, "receipt")
    receipt = await _load_public_receipt(token)
    avoided = float(
        receipt.get("estimated_provider_avoided_usd")
        or receipt.get("estimated_upstream_avoided_usd")
        or 0
    )
    return {
        "schemaVersion": 1,
        "label": "withOhm",
        "message": f"saved ${avoided:,.2f}",
        "color": "orange",
        "cacheSeconds": 3600,
    }


@app.get("/v1/public/stats")
async def public_stats(request: Request) -> dict[str, Any]:
    """Anonymous cross-tenant savings counter for the site."""
    await _public_rate_limit(request, "stats")
    agg = await state.meter.global_savings()
    return {
        **agg,
        "estimate_only": True,
        "message": (
            "Estimated provider spend avoided across all withOhm tenants via "
            "identical-request cache replay (blended list rate × hit tokens). "
            "Estimates only."
        ),
    }


@app.get("/v1/public/honesty")
async def public_honesty(request: Request) -> dict[str, Any]:
    """Published limits and non-goals — the claims we ask you NOT to take on faith.

    Anonymous by design: every entry pairs a stated limit or refusal with the
    surface that proves or enforces it, so the pipe's honesty is checkable
    rather than asserted. Marketing may quote this endpoint; it may not
    contradict it.
    """
    await _public_rate_limit(request, "honesty")
    s = state.settings
    return {
        "service": "ohm",
        "region": s.at_region,
        "limits": [
            {
                "claim": "Mid-stream provider handoff after the first byte is NOT supported",
                "verify": "GET /ready → mvp.mid_stream_failover=false (pre-first-byte retry IS shipped)",
            },
            {
                "claim": "Caching is exact-match identical-request replay only — no semantic cache",
                "verify": "GET /v1/compliance/policy → cache_purpose",
            },
            {
                "claim": "Savings figures are estimates, never a guarantee",
                "verify": "GET /v1/savings → estimate_only=true on every payload",
            },
        ],
        "refusals": [
            {
                "claim": "HTTP 402 pay-per-crawl is honored — Ohm never auto-pays or evades",
                "verify": "GET /v1/compliance/policy → pay_per_crawl=surface_402_no_autopay",
            },
            {
                "claim": "robots.txt is respected fail-closed; 401/403 revocations end the fetch",
                "verify": "GET /v1/compliance/policy → respect_robots, rules",
            },
            {
                "claim": "The cache is never exported as a training corpus",
                "verify": "GET /v1/compliance/policy → allow_cache_training=false",
            },
        ],
        "proofs": {
            "cache_hit_receipts": {
                "enabled": receipts.receipts_enabled(),
                "header": receipts.RECEIPT_HEADER,
                "format": "compact JWS (EdDSA/Ed25519)",
                "keys": "/.well-known/http-message-signatures-directory",
                "docs": "docs/RECEIPTS.md",
            },
            "web_bot_auth": {
                "enabled": web_bot_auth.signing_enabled(),
                "protocol": "rfc9421-http-message-signatures",
                "keys": "/.well-known/http-message-signatures-directory",
            },
            "nightly_golden_path": (
                "https://github.com/iwasinnam2/ohm/actions/workflows/golden-path.yml"
            ),
        },
        "note": "If a claim here stops being true, that is an incident, not a copy edit.",
    }


@app.get("/v1/ledger")
async def tenant_ledger(
    cost_center: str = "",
    limit: int = 200,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Tenant-scoped clean ledger (use /v1/org/ledger when org-bound)."""
    _key, tenant = auth
    await rate_limit(_key, tenant.tenant_id)
    org_id = tenant.org_id or ""
    summary = await state.ledger.summarize(
        org_id=org_id,
        tenant_id=tenant.tenant_id if not org_id else "",
        cost_center=cost_center or tenant.cost_center or "",
    )
    events = await state.ledger.list_events(
        org_id=org_id,
        tenant_id=tenant.tenant_id if not org_id else "",
        cost_center=cost_center or "",
        limit=min(max(limit, 1), 5000),
    )
    return {
        "tenant_id": tenant.tenant_id,
        "org_id": org_id or None,
        "cost_center": tenant.cost_center,
        "summary": summary,
        "events": state.ledger.export_json(events),
    }


@app.get("/v1/ledger/hit-ratio")
async def tenant_ledger_hit_ratio(
    month: str = "",
    group_by: str = "path",
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """Tenant-scoped hit-ratio (Intermediate solo seats without org)."""
    _key, tenant = auth
    await rate_limit(_key, tenant.tenant_id)
    gb = (group_by or "path").strip().lower()
    if gb not in ("cost_center", "path"):
        raise HTTPException(
            status_code=400, detail="group_by must be cost_center or path"
        )
    m = (month or "").strip() or time.strftime("%Y-%m", time.gmtime())
    since_ts, until_ts = month_utc_bounds(m)
    org_id = tenant.org_id or ""
    summary = await state.ledger.summarize(
        org_id=org_id,
        tenant_id=tenant.tenant_id if not org_id else "",
        since_ts=since_ts,
        until_ts=until_ts,
    )
    report = state.ledger.hit_ratio_report(summary, group_by=gb)
    return {
        "tenant_id": tenant.tenant_id,
        "org_id": org_id or None,
        "month": m,
        "since_ts": since_ts,
        "until_ts": until_ts,
        "timezone": "UTC",
        **report,
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
                "managed_keys": bool(s.at_enterprise_managed_keys),
                "sla": "target_99_9",
                "sla_note": s.at_enterprise_sla_note,
                "includes": [
                    "sso_oidc",
                    "scim_user_provisioning",
                    "org_console",
                    "corporate_clean_ledger",
                    "cost_center_attribution",
                    "audit_logs",
                    "managed_provider_keys",
                    "org_policy_profiles",
                    "agent_shell",
                ],
                "delivered": {
                    "audit_logs": bool(s.at_enterprise_audit_logs),
                    "managed_keys": bool(s.at_enterprise_managed_keys),
                    "sso": True,
                    "scim": True,
                    "clean_ledger": True,
                    "org_policy": True,
                },
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
            **{
                vendor: {
                    "configured": bool(shell._api_key),
                    "ready": True,
                    "base_url": shell._base_url,
                    "byok": True,
                    "protocol": "openai-compatible",
                }
                for vendor, shell in state.compat.items()
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
        "web_bot_auth": {
            "enabled": web_bot_auth.signing_enabled(),
            "protocol": "rfc9421-http-message-signatures",
            "tag": "web-bot-auth",
            "key_directory": "/.well-known/http-message-signatures-directory",
        },
        "pay_per_crawl": "surface_402_no_autopay",
        "rules": [
            "Public http(s) pages only — no login, credentials, tokens, or private hosts",
            "No lead harvesting, person dossiers, biometrics, or PECR cold outreach lists",
            "Short excerpts only — copyright / database-right minimisation",
            "Cache is identical-request replay only — never a training corpus",
            "UK: public identifiable data remains personal data; outputs are minimised",
            "US: CFAA/CCPA — public retrieval ≠ authorization to bypass gates",
            "robots.txt respected by default; cite sources; no private-fact invention",
            "OhmBot identifies itself (UA + Web Bot Auth signatures when keyed)",
            "HTTP 402 pay-per-crawl and 401/403 revocations are honored — no auto-pay, no evasion",
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
    org_id: str = ""
    cost_center: str = "default"


class TenantStatusBody(BaseModel):
    status: str


class CheckoutBody(BaseModel):
    plan: str = "payg"
    success_url: str = ""
    cancel_url: str = ""


class PublicCheckoutBody(BaseModel):
    plan: str = "payg"
    # Optional commit tier (rate card v2): c29 | c99 | c499. Swaps the $0
    # membership seat for a monthly commit with included metered usage.
    commit: str = ""
    label: str = ""
    email: str = ""
    terms_ack: bool = False
    dpa_ack: bool = False
    success_url: str = ""
    cancel_url: str = ""


@app.post("/v1/billing/checkout")
async def public_create_checkout(
    body: PublicCheckoutBody,
    request: Request,
) -> dict[str, Any]:
    """
    Self-serve: issue Ohm tenant key once + Stripe Checkout URL.
    Admin checkout remains an ops escape hatch.
    """
    # Soft abuse control on unauthenticated key mint (IP token bucket).
    client_ip = (
        (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "")
        or "unknown"
    )
    mint_ok = await state.store.eval_token_bucket(
        f"at:global:rl:checkout:{client_ip}",
        0.1,  # ~6/min sustained
        3.0,  # burst of 3
        time.time(),
    )
    if not mint_ok:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "checkout_rate_limit",
                "message": "Too many checkout attempts from this network. Try again shortly.",
            },
        )
    s = state.settings
    if body.plan not in ("payg", "enterprise"):
        raise HTTPException(status_code=400, detail="plan must be payg or enterprise")
    commit = body.commit.strip().lower()
    if commit and commit not in ("c29", "c99", "c499"):
        raise HTTPException(
            status_code=400, detail="commit must be c29, c99, or c499"
        )
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
            commit=commit,
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


class TopupBody(BaseModel):
    success_url: str = ""
    cancel_url: str = ""


@app.post("/v1/billing/topup")
async def credit_pack_topup(
    body: TopupBody,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
) -> dict[str, Any]:
    """RETIRED (rate card v2): the $29 credit pack is superseded by commit
    tiers, which include metered usage every cycle instead of a one-off
    voucher. Returns 410 with upgrade guidance."""
    api_key, tenant_rec = auth
    await rate_limit(api_key, tenant_rec.tenant_id)
    raise HTTPException(
        status_code=410,
        detail={
            "code": "credit_pack_retired",
            "message": (
                "The one-time credit pack is retired. Commit tiers include "
                "metered usage every month (c29: $29/mo with $35 included; "
                "c99: $99/mo with $125; c499: $499/mo with $700). "
                "See https://www.withohm.dev/subscriptions"
            ),
            "commit_tiers": ["c29", "c99", "c499"],
        },
    )


@app.get("/v1/admin/ops")
async def admin_ops(_admin: str = Depends(admin_dep)) -> dict[str, Any]:
    """Observer watchdog snapshot: billing pipeline + aggregate health.

    Scraped every 15 minutes by the observer-pulse workflow so a growing
    Stripe meter DLQ (silent underbilling) pages within one probe interval
    instead of surfacing at invoice time.
    """
    redis_ok = False
    try:
        redis_ok = bool(await state.store.ping())
    except Exception:  # noqa: BLE001 — report, don't crash the probe
        redis_ok = False
    dlq_len = 0
    try:
        dlq_len = await state.store.list_len(STRIPE_METER_DLQ_KEY)
    except Exception:  # noqa: BLE001
        dlq_len = -1  # unreadable — probe treats as failure
    agg = await state.meter.global_savings()
    tenant_keys = await state.store.scan_keys("at:*:meta:record", limit=10_000)
    return {
        "ok": redis_ok and dlq_len == 0,
        "ts": int(time.time()),
        "region": state.settings.at_region,
        "redis_ok": redis_ok,
        "stripe_meter_dlq_len": dlq_len,
        "tenant_records": len(tenant_keys),
        "global": agg,
        "thresholds": {
            "stripe_meter_dlq_len": "0 expected; >0 means meter events failed and await replay",
        },
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
        org_id=body.org_id,
        cost_center=body.cost_center or "default",
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
            "mode",
            "amount_total",
            "currency",
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

    # $29 credit pack (mode=payment): apply as customer balance credit so it
    # offsets future metered invoices, then attach the customer and stop —
    # a one-time payment is not a subscription status signal.
    if (
        event_type == "checkout.session.completed"
        and meta.get("purpose") == "credit_pack"
    ):
        credited = stripe_billing.apply_credit_pack_balance(
            state.settings,
            stripe_customer_id=str(customer_id or ""),
            amount_cents=int(obj.get("amount_total") or 0),
            currency=str(obj.get("currency") or "usd"),
        )
        if tenant_id and customer_id:
            await state.tenants.attach_stripe(
                tenant_id,
                customer_id=str(customer_id),
                subscription_id="",
                plan=None,
                status=None,
                billing_paid=None,
            )
        log.info(
            "credit pack webhook tenant=%s customer=%s credited=%s",
            tenant_id,
            customer_id,
            credited,
        )
        return {"received": True, "type": event_type, "credit_pack": credited}

    # Seat-only Checkout: attach hit/miss/fetch meter Prices after the card
    # is collected so the hosted page does not list them as charges.
    if event_type == "checkout.session.completed" and subscription_id:
        attached = stripe_billing.attach_meter_prices_to_subscription(
            state.settings, subscription_id=str(subscription_id)
        )
        log.info(
            "checkout meters attached tenant=%s sub=%s new_items=%s",
            tenant_id,
            subscription_id,
            attached,
        )

    new_status = stripe_billing.apply_webhook_to_status(
        event_type, subscription_status=subscription_status
    )
    billing_paid: bool | None = None
    clear_delinquent = False
    delinquent_since: int | None = None

    if event_type == "invoice.paid":
        billing_paid = True
        clear_delinquent = True
        # Commit tier (rate card v2): each paid cycle grants the included
        # metered usage as a billing credit scoped to metered prices.
        # Idempotent per invoice — webhook redelivery cannot double-grant.
        commit_tier = stripe_billing.commit_tier_for_invoice(
            state.settings, data_obj
        )
        if commit_tier and customer_id:
            invoice_id = str(obj.get("id") or "")
            granted = stripe_billing.grant_commit_included_credit(
                state.settings,
                stripe_customer_id=str(customer_id),
                tier=commit_tier,
                invoice_id=invoice_id,
            )
            log.info(
                "commit credit tenant=%s customer=%s tier=%s invoice=%s granted_usd=%s",
                tenant_id,
                customer_id,
                commit_tier,
                invoice_id,
                granted,
            )
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


async def _open_stream_with_retry(
    provider: Any,
    *,
    model: str,
    messages: list[dict[str, Any]],
    kwargs: dict[str, Any],
) -> tuple[AsyncIterator[str], Optional[str]]:
    """Open an upstream SSE stream and eagerly pull the first line.

    Pre-first-byte failover: if the upstream fails before emitting anything
    (connect error or upstream HTTP error), retry once on a fresh connection.
    A second pre-first-byte failure raises ProviderUpstreamError so the caller
    can return an honest HTTP error status instead of a 200 stream that only
    carries an error frame. Mid-stream handoff after the first byte remains
    out of scope (`mid_stream_failover: false`).
    """
    last_exc: Exception | None = None
    for attempt in range(2):
        stream = await provider.chat_completion(
            model=model, messages=messages, stream=True, **kwargs
        )
        try:
            first = await stream.__anext__()  # type: ignore[union-attr]
        except StopAsyncIteration:
            return stream, None
        except ProviderUpstreamError as exc:
            last_exc = exc
            log.warning(
                "stream pre-first-byte upstream error attempt=%d provider=%s: %s",
                attempt + 1,
                exc.provider,
                exc,
            )
            continue
        except httpx.HTTPError as exc:
            last_exc = exc
            log.warning(
                "stream pre-first-byte transport error attempt=%d: %s", attempt + 1, exc
            )
            continue
        text = first if isinstance(first, str) else first.decode("utf-8", errors="replace")
        return stream, text
    if isinstance(last_exc, ProviderUpstreamError):
        raise last_exc
    raise ProviderUpstreamError(
        getattr(provider, "name", "upstream"),
        502,
        {"error": {"message": str(last_exc) if last_exc else "upstream stream failed"}},
    )


class EdgeHitBody(BaseModel):
    total_tokens: int = 0
    # Optional receipt context from the edge (model + cache-key digest) so
    # edge-served HITs carry the same signed proof as control-plane HITs.
    model: str = ""
    request_sha256: str = ""


@app.post("/internal/edge-hit")
async def edge_hit_meter(
    body: EdgeHitBody,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
    x_ohm_edge_secret: Optional[str] = Header(
        default=None, alias="X-Ohm-Edge-Secret"
    ),
) -> dict[str, Any]:
    """Meter + enforce a Rust-edge cache HIT.

    The edge calls this before serving a cached completion so HITs are billed
    and suspended/capped tenants are denied even on the cached path. The
    ``auth_tenant`` dependency raises 401/402/403 for the edge to relay; a 200
    means "serve the cached body". Requires the shared edge secret — when it is
    unset the endpoint is disabled (503) and the edge must full-proxy instead.
    """
    s = state.settings
    if not s.at_edge_shared_secret:
        raise HTTPException(
            status_code=503,
            detail="Edge HIT metering disabled (AT_EDGE_SHARED_SECRET unset)",
        )
    if x_ohm_edge_secret != s.at_edge_shared_secret:
        raise HTTPException(status_code=403, detail="Invalid edge secret")
    api_key, tenant_rec = auth
    await rate_limit(api_key, tenant_rec.tenant_id)
    event = await state.meter.record_chat(
        tenant_rec.tenant_id,
        cache_hit=True,
        total_tokens=max(0, int(body.total_tokens)),
        stripe_customer_id=tenant_rec.stripe_customer_id or "",
    )
    await _append_ledger(
        tenant_rec,
        kind="cache_hit",
        tokens=max(0, int(body.total_tokens)),
        pipe_usd=event.billed_usd,
        cache_hit=True,
    )
    out: dict[str, Any] = {
        "ok": True,
        "billed_usd": event.billed_usd,
        "stripe_synced": event.stripe_synced,
    }
    receipt_jws = receipts.mint_receipt(
        tenant=tenant_rec.tenant_id,
        model=body.model,
        tokens_replayed=body.total_tokens,
        pipe_usd=event.billed_usd,
        request_sha256=body.request_sha256,
        region=state.settings.at_region,
        plane="rust-edge",
    )
    if receipt_jws:
        out["receipt"] = receipt_jws
    return out


@app.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    auth: tuple[str, TenantRecord] = Depends(auth_tenant),
    x_ohm_upstream_key: Optional[str] = Header(default=None, alias="X-Ohm-Upstream-Key"),
    x_ohm_path: Optional[str] = Header(default=None, alias="X-Ohm-Path"),
):
    api_key, tenant_rec = auth
    await rate_limit(api_key, tenant_rec.tenant_id)
    await _org_policy_gate(tenant_rec, body)
    tenant = tenant_rec.tenant_id
    stripe_customer = tenant_rec.stripe_customer_id or ""
    traffic_path = normalize_path(x_ohm_path or body.ohm_path)
    messages = [m.model_dump() for m in body.messages]
    upstream_key = (x_ohm_upstream_key or "").strip()
    # Enterprise managed pool / org policy may omit BYOK and use Ohm env keys
    org_managed = False
    if tenant_rec.org_id:
        _org = await state.orgs.get(tenant_rec.org_id)
        org_managed = bool(_org and _org.policy_obj().managed_keys)
    allow_fallback = state.settings.at_byok_allow_env_fallback or (
        tenant_rec.plan in ("enterprise", "dev")
    ) or (
        org_managed and state.settings.at_enterprise_managed_keys
    )

    assert_cache_training_denied(state.settings.at_compliance_allow_cache_training)
    no_store = (body.cache_control or "").strip().lower() == "no_store"
    if tenant_rec.org_id and not no_store:
        _org2 = await state.orgs.get(tenant_rec.org_id)
        if _org2 and _org2.policy_obj().default_cache_no_store:
            no_store = True

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
        # Unlock requires a *paid* invoice (or a privileged plan). Metered spend
        # alone must never lift the cap — un-invoiced usage is not payment.
        unlocked = (
            tenant_rec.billing_paid
            or tenant_rec.plan in ("enterprise", "dev", "design_partner")
        )
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
                            "usage unlock. Complete Checkout — the first paid "
                            "invoice lifts this cap. See /docs/pricing."
                        ),
                        "today_fetches": today,
                        "cap": cap,
                    },
                )
        # Tenant Checkout/admin mint stores terms_version + dpa_version.
        # Per-request acks still win; otherwise honor bound tenant versions.
        s = state.settings
        tenant_terms_ok = bool(
            (tenant_rec.terms_version or "") == s.at_compliance_terms_version
            and (tenant_rec.dpa_version or "") == s.at_compliance_dpa_version
        )
        terms_ack = bool(body.terms_ack) or tenant_terms_ok
        dpa_ack = bool(body.dpa_ack) or tenant_terms_ok
        # Binding ToS at seat mint covers public-only compliance for allowed purposes.
        compliance_ack = bool(body.web_compliance_ack) or tenant_terms_ok
        ctx = await fetch_web_context(
            state.settings,
            query=body.web_query,
            urls=body.web_urls or None,
            purpose=body.web_purpose,
            compliance_ack=compliance_ack,
            terms_ack=terms_ack,
            dpa_ack=dpa_ack,
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
                fev = await state.meter.record_fetch(
                    tenant, fetch_count, stripe_customer_id=stripe_customer
                )
                await _append_ledger(
                    tenant_rec,
                    kind="fetch",
                    model=body.model,
                    fetches=fetch_count,
                    pipe_usd=fev.billed_usd,
                    purpose=str(web_purpose or ""),
                    path=traffic_path,
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
        "X-Ohm-Path": traffic_path,
        "X-Ohm-Cost-Center": tenant_rec.cost_center or "default",
    }

    if not no_store:
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
            await _append_ledger(
                tenant_rec,
                kind="cache_hit",
                model=body.model,
                tokens=total,
                pipe_usd=event.billed_usd,
                cache_hit=True,
                purpose=str(web_purpose or ""),
                path=traffic_path,
            )
            hit_headers = {
                **cache_headers,
                "X-AT-Cache": "HIT",
                "X-AT-Billed-USD": f"{event.billed_usd:.6f}",
            }
            # Signed proof of the replay: verifiable against the public JWKS
            # at /.well-known/http-message-signatures-directory.
            receipt_jws = receipts.mint_receipt(
                tenant=tenant,
                model=body.model,
                tokens_replayed=total,
                pipe_usd=event.billed_usd,
                request_sha256=receipts.request_digest_from_cache_key(ckey),
                region=state.settings.at_region,
                plane="python",
            )
            if receipt_jws:
                hit_headers[receipts.RECEIPT_HEADER] = receipt_jws
            if body.stream:
                # Streamed replay: same cache entry, delivered as SSE.
                replay_lines = sse_lines_from_completion(payload)

                async def replay_stream() -> AsyncIterator[bytes]:
                    for line in replay_lines:
                        yield line.encode("utf-8")

                return StreamingResponse(
                    replay_stream(),
                    media_type="text/event-stream",
                    headers={**hit_headers, "Cache-Control": "no-cache"},
                )
            return JSONResponse(payload, headers=hit_headers)

    if model_needs_upstream(body.model) and not provider_key_available(
        body.model,
        upstream_key=upstream_key,
        openai=state.openai,
        anthropic=state.anthropic,
        allow_env_fallback=allow_fallback,
        compat=state.compat,
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

    spend_cap_headers = await _spend_cap_on_miss(tenant_rec)
    cache_headers = {**cache_headers, **spend_cap_headers}

    provider, model = resolve_provider(
        body.model,
        openai=state.openai,
        anthropic=state.anthropic,
        mock=state.mock,
        fallback=state.settings.at_fallback_model,
        upstream_key=upstream_key,
        allow_env_fallback=allow_fallback,
        compat=state.compat,
    )

    kwargs: dict[str, Any] = {}
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    try:
        if body.stream:
            # Pre-first-byte failover: pull the first SSE line eagerly so an
            # upstream that dies before emitting anything gets one clean retry
            # and, failing that, an honest HTTP error status — never a 200
            # stream that only carries an error frame.
            stream, first_line = await _open_stream_with_retry(
                provider, model=model, messages=messages, kwargs=kwargs
            )

            async def event_stream() -> AsyncIterator[bytes]:
                collected: list[str] = []
                usage_total: int | None = None
                try:
                    if first_line is not None:
                        collected.append(first_line)
                        parsed_first = usage_from_sse_line(first_line)
                        if parsed_first is not None:
                            usage_total = parsed_first
                        yield first_line.encode("utf-8")
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
                sev = await state.meter.record_chat(
                    tenant,
                    cache_hit=False,
                    total_tokens=total_tokens,
                    stripe_customer_id=stripe_customer,
                )
                await _append_ledger(
                    tenant_rec,
                    kind="cache_miss",
                    model=body.model,
                    tokens=total_tokens,
                    pipe_usd=sev.billed_usd,
                    cache_hit=False,
                    purpose=str(web_purpose or ""),
                    path=traffic_path,
                )
                if not no_store:
                    # Streamed MISS populates the same cache entry the JSON
                    # path uses; assembly returns None unless the stream
                    # finished cleanly (finish_reason seen), so truncated
                    # streams are never cached.
                    assembled = assemble_completion_from_sse_lines(collected)
                    if assembled is not None:
                        await state.store.set(
                            ckey,
                            json.dumps(assembled),
                            ttl_seconds=state.settings.at_cache_ttl_seconds,
                        )

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    **cache_headers,
                    "X-AT-Cache": "BYPASS" if no_store else "MISS",
                    "X-Ohm-Stream-Failover": "pre-first-byte",
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
    await _append_ledger(
        tenant_rec,
        kind="cache_miss",
        model=body.model,
        tokens=total,
        pipe_usd=event.billed_usd,
        cache_hit=False,
        purpose=str(web_purpose or ""),
        path=traffic_path,
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
