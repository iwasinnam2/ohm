"""Ohm MCP server — Cursor attach for cache + compliant web fetch.

Transports:
  * stdio (default) — local Cursor attach; auth via OHM_API_KEY env.
  * streamable HTTP (stateless) — remote attach per MCP 2026-07-28 stateless
    core; auth via the incoming `Authorization: Bearer sk-at-*` header
    (per-request pass-through), falling back to OHM_API_KEY env.

Run remote: `OHM_MCP_TRANSPORT=http ohm-mcp` (or `ohm-mcp-http`).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

try:
    from mcp.server import MCPServer
    from mcp.server.mcpserver import Context
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Install MCP extra: pip install 'at-utility[mcp]' "
        "(or: pip install \"at-utility[mcp] @ git+https://github.com/iwasinnam2/ohm.git\")"
    ) from exc

mcp = MCPServer("ohm")

DEFAULT_BASE = "https://api.withohm.dev/v1"
UPSTREAM_HEADER = "X-Ohm-Upstream-Key"


def _header_lookup(ctx: Optional[Context], name: str) -> str:
    """Case-insensitive header read from the transport (None on stdio)."""
    headers = getattr(ctx, "headers", None) if ctx is not None else None
    if not headers:
        return ""
    lowered = name.lower()
    for k, v in headers.items():
        if k.lower() == lowered:
            return (v or "").strip()
    return ""


def _cfg(ctx: Optional[Context] = None) -> tuple[str, str, str]:
    base = (os.environ.get("OHM_BASE_URL") or DEFAULT_BASE).rstrip("/")
    # Remote (HTTP) attach: per-request Authorization pass-through wins so a
    # single stateless deployment can serve many tenants without shared keys.
    key = ""
    bearer = _header_lookup(ctx, "Authorization")
    if bearer.lower().startswith("bearer "):
        key = bearer[7:].strip()
    if not key:
        key = (os.environ.get("OHM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "Ohm API key required: send 'Authorization: Bearer sk-at-*' on the "
            "MCP HTTP request, or set OHM_API_KEY env for stdio. Create a seat "
            "at https://www.withohm.dev/billing/intermediate "
            "(do not use local bootstrap sk-at-dev in production)."
        )
    upstream = _header_lookup(ctx, UPSTREAM_HEADER) or os.environ.get(
        "OHM_UPSTREAM_KEY", ""
    )
    return base, key, upstream


def _headers(upstream: str = "", ctx: Optional[Context] = None) -> dict[str, str]:
    _, key, env_up = _cfg(ctx)
    h = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    up = upstream or env_up
    if up:
        h[UPSTREAM_HEADER] = up
    return h


@mcp.tool()
async def ohm_fetch_web(
    urls: list[str],
    purpose: str = "public_web_retrieval",
    query: str = "",
    format: str = "markdown",
    ctx: Optional[Context] = None,
) -> str:
    """
    Compliant public-web fetch via Ohm ingest (metered ohm_web_fetch).

    Terms/DPA must already be bound on the tenant at Checkout (or admin mint).
    This tool does not forge per-request legal acks.

    Args:
      urls: Public http(s) pages to fetch.
      purpose: One of public_web_retrieval, business_catalog,
        public_company_info, job_listings.
      query: Optional focus question for the model summarizer.
      format: markdown (default) or json — json returns title/text/meta/json_ld
        structure injected as context.

    Returns redacted markdown or JSON-shaped context (model summary when via chat).
    """
    base, _, _ = _cfg(ctx)
    fmt = (format or "markdown").strip().lower()
    if fmt not in ("markdown", "json"):
        fmt = "markdown"
    body: dict[str, Any] = {
        "model": "mock",
        "messages": [{"role": "user", "content": query or "Summarize the web context."}],
        "fetch_web_context": True,
        "web_purpose": purpose,
        "web_urls": urls,
        "web_format": fmt,
        "cache_control": "no_store",
    }
    if query:
        body["web_query"] = query
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            f"{base}/chat/completions", headers=_headers(ctx=ctx), json=body
        )
        if res.status_code >= 400:
            return json.dumps({"error": res.text, "status": res.status_code})
        data = res.json()
        content = (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
            or ""
        )
        return content or json.dumps(data)


@mcp.tool()
async def ohm_usage(ctx: Optional[Context] = None) -> str:
    """Return Ohm usage snapshot: cache hit ratio, fetches, estimated pipe rent (GET /v1/usage)."""
    base, _, _ = _cfg(ctx)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base}/usage", headers=_headers(ctx=ctx))
        return res.text


@mcp.tool()
async def ohm_chat(
    prompt: str,
    model: str = "mock",
    fetch_urls: Optional[list[str]] = None,
    purpose: str = "public_web_retrieval",
    upstream_api_key: str = "",
    ctx: Optional[Context] = None,
) -> str:
    """
    Chat through Ohm (OpenAI-compatible). Identical prompts hit Redis cache.

    When fetch_urls is set, Terms/DPA must already be bound on the tenant
    (Checkout). This tool does not forge per-request legal acks.

    Args:
      prompt: User message.
      model: Upstream model id (mock for local; gpt/claude need BYOK).
      fetch_urls: Optional public URLs to attach as compliant web context.
      purpose: Ingest purpose when fetch_urls is set.
      upstream_api_key: Optional BYOK override (else OHM_UPSTREAM_KEY).
    """
    base, _, _ = _cfg(ctx)
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if fetch_urls:
        body.update(
            {
                "fetch_web_context": True,
                "web_purpose": purpose,
                "web_urls": fetch_urls,
            }
        )
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            f"{base}/chat/completions",
            headers=_headers(upstream_api_key, ctx=ctx),
            json=body,
        )
        if res.status_code >= 400:
            return json.dumps({"error": res.text, "status": res.status_code})
        data = res.json()
        return (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
            or json.dumps(data)
        )


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


DEFAULT_ALLOWED_HOSTS = "mcp.withohm.dev,api.withohm.dev,localhost,127.0.0.1"


def _transport_security():
    """DNS-rebinding protection with configurable Host/Origin allowlists."""
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = [
        h.strip()
        for h in (
            os.environ.get("OHM_MCP_ALLOWED_HOSTS") or DEFAULT_ALLOWED_HOSTS
        ).split(",")
        if h.strip()
    ]
    origins = [
        o.strip()
        for o in (os.environ.get("OHM_MCP_ALLOWED_ORIGINS") or "").split(",")
        if o.strip()
    ]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        # Bare hostnames also allow host:port forms
        allowed_hosts=sorted({*hosts, *(f"{h}:*" for h in hosts if ":" not in h)}),
        allowed_origins=origins,
    )


def http_app(*, json_response: bool = True):
    """Stateless streamable-HTTP ASGI app (MCP 2026-07-28 stateless core).

    No session identifiers, no server-held stream state: cacheable, routable,
    horizontally scalable behind any load balancer. Mount at `/mcp`.
    """
    return mcp.streamable_http_app(
        stateless_http=True,
        json_response=json_response,
        transport_security=_transport_security(),
    )


def main() -> None:
    """Entry point. OHM_MCP_TRANSPORT=stdio (default) | http | streamable-http."""
    transport = (os.environ.get("OHM_MCP_TRANSPORT") or "stdio").strip().lower()
    if transport in ("http", "streamable-http", "streamable_http"):
        main_http()
        return
    mcp.run()


def main_http() -> None:
    """Run the stateless remote MCP server over streamable HTTP."""
    mcp.run(
        "streamable-http",
        host=os.environ.get("OHM_MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("OHM_MCP_PORT", "8091")),
        stateless_http=True,
        json_response=_env_flag("OHM_MCP_JSON_RESPONSE", True),
        transport_security=_transport_security(),
    )


if __name__ == "__main__":
    main()
