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
        "Install MCP extra: pip install 'at-utility[mcp]' (or pip install mcp>=2)"
    ) from exc

mcp = MCPServer("ohm")

DEFAULT_BASE = "http://127.0.0.1:8081/v1"
UPSTREAM_HEADER = "X-Ohm-Upstream-Key"


def _cfg() -> tuple[str, str, str]:
    base = os.environ.get("OHM_BASE_URL", DEFAULT_BASE).rstrip("/")
    key = os.environ.get("OHM_API_KEY", "sk-at-dev")
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
) -> str:
    """
    Fetch public web pages through Ohm's compliant ingest and return redacted
    markdown context. Allowed purposes: public_web_retrieval, business_catalog,
    public_company_info, job_listings. This is metered (ohm_web_fetch).
    """
    base, _, _ = _cfg()
    body: dict[str, Any] = {
        "model": "mock",
        "messages": [{"role": "user", "content": query or "Summarize the web context."}],
        "fetch_web_context": True,
        "web_purpose": purpose,
        "web_urls": urls,
        "web_compliance_ack": True,
        "terms_ack": True,
        "dpa_ack": True,
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


@mcp.tool()
async def ohm_usage() -> str:
    """Return Ohm usage snapshot: cache hit ratio, fetches, web attach rate."""
    base, _, _ = _cfg()
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base}/usage", headers=_headers())
        return res.text


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
    Pass fetch_urls to attach compliant public web context. For gpt/claude
    models, set OHM_UPSTREAM_KEY or upstream_api_key (BYOK).
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
                "web_compliance_ack": True,
                "terms_ack": True,
                "dpa_ack": True,
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
