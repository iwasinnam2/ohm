"""Ohm MCP server — Cursor attach for cache + compliant web fetch."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

try:
    from mcp.server import MCPServer
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "MCP support missing: pip install withohm-mcp "
        "(or, in the monorepo: pip install 'at-utility[mcp]')"
    ) from exc

mcp = MCPServer("ohm")

DEFAULT_BASE = "https://api.withohm.dev/v1"
UPSTREAM_HEADER = "X-Ohm-Upstream-Key"


def _cfg() -> tuple[str, str, str]:
    base = (os.environ.get("OHM_BASE_URL") or DEFAULT_BASE).rstrip("/")
    key = (os.environ.get("OHM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "OHM_API_KEY is required. Create a seat at "
            "https://www.withohm.dev/billing/intermediate and set the issued key "
            "in Cursor MCP env (do not use local bootstrap sk-at-dev in production)."
        )
    upstream = os.environ.get("OHM_UPSTREAM_KEY", "")
    return base, key, upstream


def _headers(upstream: str = "") -> dict[str, str]:
    _, key, env_up = _cfg()
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
    base, _, _ = _cfg()
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
            f"{base}/chat/completions", headers=_headers(), json=body
        )
        if res.status_code >= 400:
            return json.dumps({"error": res.text, "status": res.status_code})
        data = res.json()
        content = (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
            or ""
        )
        return content or json.dumps(data)


async def _get(path: str) -> str:
    base, _, _ = _cfg()
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base}{path}", headers=_headers())
        return res.text


@mcp.tool()
async def ohm_usage() -> str:
    """Return Ohm usage snapshot: cache hit ratio, fetches, estimated pipe rent (GET /v1/usage)."""
    return await _get("/usage")


@mcp.tool()
async def ohm_models() -> str:
    """List the model ids the Ohm pipe routes to, including BYOK upstreams (GET /v1/models)."""
    return await _get("/models")


@mcp.tool()
async def ohm_savings() -> str:
    """Return the cache savings snapshot: replayed prompts and estimated spend avoided (GET /v1/savings)."""
    return await _get("/savings")


@mcp.tool()
async def ohm_providers() -> str:
    """Return upstream provider and failover status for the Ohm pipe (GET /v1/providers)."""
    return await _get("/providers")


@mcp.tool()
async def ohm_policy() -> str:
    """Return the compliance policy: which web-fetch purposes are allowed and their limits (GET /v1/compliance/policy)."""
    return await _get("/compliance/policy")


@mcp.tool()
async def ohm_chat(
    prompt: str,
    model: str = "mock",
    fetch_urls: Optional[list[str]] = None,
    purpose: str = "public_web_retrieval",
    upstream_api_key: str = "",
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
    base, _, _ = _cfg()
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
            headers=_headers(upstream_api_key),
            json=body,
        )
        if res.status_code >= 400:
            return json.dumps({"error": res.text, "status": res.status_code})
        data = res.json()
        return (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
            or json.dumps(data)
        )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
