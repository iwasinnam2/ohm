"""Playwright + meta-search ingestion worker (public-only, compliance-gated)."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Allow `python workers/ingest_worker.py` without installing the package.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from at_utility.compliance import (  # noqa: E402
    ComplianceError,
    apply_excerpt_cap,
    evaluate_ingest_request,
    gate_url,
    redact_personal_data,
)
from at_utility.compliance.robots import USER_AGENT, allowed_by_robots  # noqa: E402
from at_utility.compliance.web_bot_auth import (  # noqa: E402
    signature_headers,
    signing_enabled,
)

log = logging.getLogger("ingest_worker")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="at-utility-ingest",
    version="0.1.0",
    description="Public-web retrieval only. See docs/LEGAL.md.",
)

TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "30000"))
SERP_PROVIDER = os.getenv("SERP_PROVIDER", "duckduckgo")
COMPLIANCE_ENFORCE = os.getenv("AT_COMPLIANCE_ENFORCE", "true").lower() in (
    "1",
    "true",
    "yes",
)
RESPECT_ROBOTS_DEFAULT = os.getenv("AT_COMPLIANCE_RESPECT_ROBOTS", "true").lower() in (
    "1",
    "true",
    "yes",
)
REDACT_PII_DEFAULT = os.getenv("AT_COMPLIANCE_REDACT_PII", "true").lower() in (
    "1",
    "true",
    "yes",
)
MAX_CHARS_PER_SOURCE = int(os.getenv("AT_COMPLIANCE_MAX_CHARS_PER_SOURCE", "4000"))
JURISDICTION = os.getenv("AT_COMPLIANCE_JURISDICTION", "uk_us")
BOT_UA = os.getenv(
    "AT_COMPLIANCE_USER_AGENT",
    USER_AGENT,
)


def _bot_headers(url: str) -> dict[str, str]:
    """Identified-crawler headers: UA + Web Bot Auth signatures when keyed."""
    return {"User-Agent": BOT_UA, **signature_headers(url)}


def _refusal_for_status(
    url: str,
    status: int,
    headers: Any,
    fmt: str,
) -> Optional[dict[str, Any]]:
    """Terminal refusals for licensed-crawl / revoked-access responses.

    HTTP 402 (Pay Per Crawl) and 401/403 are honored as the origin's decision:
    Ohm does not auto-pay and does not retry around technical blocks
    (docs/LEGAL.md). The publisher's price signal is surfaced when present.
    """
    empty = {"json": {}} if fmt == "json" else {"markdown": ""}

    def _h(name: str) -> Optional[str]:
        try:
            value = headers.get(name) if headers is not None else None
        except Exception:  # noqa: BLE001
            value = None
        return value

    if status == 402:
        price = _h("crawler-price") or _h("crawler-exact-price")
        return {
            "url": url,
            "ok": False,
            "error": (
                "Payment required (HTTP 402): origin requests licensed access "
                "(pay-per-crawl). Ohm does not auto-pay; fetch not performed."
            ),
            "compliance": {
                "code": "payment_required_402",
                "allowed": False,
                "http_status": 402,
                "pay_per_crawl": True,
                "crawler_price": price,
                "web_bot_auth": signing_enabled(),
            },
            **empty,
        }
    if status in (401, 403):
        return {
            "url": url,
            "ok": False,
            "error": (
                f"Access denied (HTTP {status}): origin refused OhmBot. "
                "Access revocation is honored — no retry or block evasion."
            ),
            "compliance": {
                "code": f"access_denied_{status}",
                "allowed": False,
                "http_status": status,
                "web_bot_auth": signing_enabled(),
            },
            **empty,
        }
    return None


class IngestRequest(BaseModel):
    query: Optional[str] = None
    urls: list[str] = Field(default_factory=list)
    format: str = "markdown"
    max_results: int = 3
    purpose: Optional[str] = None
    compliance_ack: bool = False
    respect_robots: Optional[bool] = None
    redact_pii: Optional[bool] = None
    jurisdiction_profile: Optional[str] = None
    max_chars_per_source: Optional[int] = None


def html_to_markdown(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    return f"# {title}\n\nSource: {url}\n\n{text[:20000]}"


def html_to_json(html: str, url: str) -> dict[str, Any]:
    """Structured scrape: title, text, meta, JSON-LD (no custom field DSL)."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = (tag.get("name") or tag.get("property") or "").strip().lower()
        content = (tag.get("content") or "").strip()
        if not name or not content:
            continue
        if name in ("description", "og:title", "og:description", "og:type", "og:url"):
            meta[name] = content

    json_ld: list[Any] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            json_ld.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    for tag in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)

    out: dict[str, Any] = {
        "url": url,
        "title": title,
        "text": text[:20000],
    }
    if meta:
        out["meta"] = meta
    if json_ld:
        out["json_ld"] = json_ld
    return out


def _redact_json_strings(value: Any, *, enabled: bool) -> tuple[Any, int]:
    """Walk JSON and redact PII in string leaves. Returns (value, total_redactions)."""
    if not enabled:
        return value, 0
    if isinstance(value, str):
        red = redact_personal_data(value, enabled=True)
        return red.text, red.total
    if isinstance(value, list):
        total = 0
        out_list = []
        for item in value:
            scrubbed, n = _redact_json_strings(item, enabled=True)
            out_list.append(scrubbed)
            total += n
        return out_list, total
    if isinstance(value, dict):
        total = 0
        out_dict: dict[str, Any] = {}
        for k, v in value.items():
            scrubbed, n = _redact_json_strings(v, enabled=True)
            out_dict[k] = scrubbed
            total += n
        return out_dict, total
    return value, 0


def _finalize_markdown(
    md: str,
    *,
    redact_pii: bool,
    max_chars: int,
    respect_robots: bool,
) -> dict[str, Any]:
    red = redact_personal_data(md, enabled=redact_pii)
    excerpt = apply_excerpt_cap(red.text, max_chars=max_chars)
    return {
        "markdown": excerpt.text,
        "compliance": {
            "allowed": True,
            "pii_redactions": red.total,
            "robots": "checked" if respect_robots else "skipped",
            "excerpt_truncated": excerpt.truncated,
            "excerpt_chars": excerpt.chars_after,
            "code_blocks_stripped": excerpt.code_blocks_stripped,
        },
    }


def _finalize_json(
    payload: dict[str, Any],
    *,
    redact_pii: bool,
    max_chars: int,
    respect_robots: bool,
) -> dict[str, Any]:
    scrubbed, pii_total = _redact_json_strings(payload, enabled=redact_pii)
    # Cap primary text field; keep structure intact for agents
    text = scrubbed.get("text") or ""
    excerpt = apply_excerpt_cap(text, max_chars=max_chars)
    scrubbed["text"] = excerpt.text
    return {
        "json": scrubbed,
        "compliance": {
            "allowed": True,
            "pii_redactions": pii_total,
            "robots": "checked" if respect_robots else "skipped",
            "excerpt_truncated": excerpt.truncated,
            "excerpt_chars": excerpt.chars_after,
            "code_blocks_stripped": excerpt.code_blocks_stripped,
        },
    }


def _finalize_content(
    html: str,
    url: str,
    *,
    fmt: str,
    redact_pii: bool,
    max_chars: int,
    respect_robots: bool,
) -> dict[str, Any]:
    if fmt == "json":
        return _finalize_json(
            html_to_json(html, url),
            redact_pii=redact_pii,
            max_chars=max_chars,
            respect_robots=respect_robots,
        )
    return _finalize_markdown(
        html_to_markdown(html, url),
        redact_pii=redact_pii,
        max_chars=max_chars,
        respect_robots=respect_robots,
    )


async def meta_search(query: str, max_results: int = 3) -> list[str]:
    """Lightweight DuckDuckGo HTML meta-search (no owned index)."""
    if SERP_PROVIDER != "duckduckgo":
        log.warning("serp provider %s not implemented; using duckduckgo", SERP_PROVIDER)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        res = await client.get(url, headers=_bot_headers(url))
        res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    links: list[str] = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href and href.startswith("http"):
            g = gate_url(href)
            if not g.allowed:
                continue
            links.append(href)
        if len(links) >= max_results:
            break
    return links


async def fetch_url(
    url: str,
    *,
    respect_robots: bool,
    redact_pii: bool,
    max_chars_per_source: int,
    fmt: str = "markdown",
) -> dict[str, Any]:
    """Prefer Playwright; fall back to httpx if browser not installed."""
    fmt = (fmt or "markdown").strip().lower()
    if fmt not in ("markdown", "json"):
        fmt = "markdown"

    g = gate_url(url)
    if not g.allowed:
        return {
            "url": url,
            "ok": False,
            "error": g.reason,
            "compliance": {"code": g.code, "allowed": False},
            **({"json": {}} if fmt == "json" else {"markdown": ""}),
        }

    if not await allowed_by_robots(url, enabled=respect_robots):
        return {
            "url": url,
            "ok": False,
            "error": "Disallowed by robots.txt for OhmBot",
            "compliance": {"code": "robots_disallow", "allowed": False},
            **({"json": {}} if fmt == "json" else {"markdown": ""}),
        }

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            sig = signature_headers(url)
            page = await browser.new_page(
                user_agent=BOT_UA,
                **({"extra_http_headers": sig} if sig else {}),
            )
            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=TIMEOUT_MS
            )
            # Honor licensed-crawl / revoked-access statuses (402 / 401 / 403)
            if response is not None:
                refusal = _refusal_for_status(url, response.status, response.headers, fmt)
                if refusal is not None:
                    await browser.close()
                    return refusal
            # Refuse if navigation landed on an obvious login wall URL
            final = page.url
            final_gate = gate_url(final)
            if not final_gate.allowed:
                await browser.close()
                return {
                    "url": url,
                    "ok": False,
                    "error": f"Navigation landed on blocked surface: {final_gate.reason}",
                    "compliance": {"code": final_gate.code, "allowed": False, "final_url": final},
                    **({"json": {}} if fmt == "json" else {"markdown": ""}),
                }
            html = await page.content()
            await browser.close()
            fin = _finalize_content(
                html,
                final,
                fmt=fmt,
                redact_pii=redact_pii,
                max_chars=max_chars_per_source,
                respect_robots=respect_robots,
            )
            return {"url": final, "ok": True, **fin}
    except Exception as exc:  # noqa: BLE001
        log.info("playwright unavailable or failed (%s); httpx fallback", exc)
        return await _fetch_via_httpx(
            url,
            fmt=fmt,
            redact_pii=redact_pii,
            max_chars_per_source=max_chars_per_source,
            respect_robots=respect_robots,
        )


async def _fetch_via_httpx(
    url: str,
    *,
    fmt: str,
    redact_pii: bool,
    max_chars_per_source: int,
    respect_robots: bool,
) -> dict[str, Any]:
    """httpx fetch path (also the Playwright fallback), Web Bot Auth signed."""
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_MS / 1000.0, follow_redirects=True
        ) as client:
            res = await client.get(url, headers=_bot_headers(url))
            refusal = _refusal_for_status(url, res.status_code, res.headers, fmt)
            if refusal is not None:
                return refusal
            res.raise_for_status()
            final = str(res.url)
            final_gate = gate_url(final)
            if not final_gate.allowed:
                return {
                    "url": url,
                    "ok": False,
                    "error": f"Redirected to blocked surface: {final_gate.reason}",
                    "compliance": {
                        "code": final_gate.code,
                        "allowed": False,
                        "final_url": final,
                    },
                    **({"json": {}} if fmt == "json" else {"markdown": ""}),
                }
            fin = _finalize_content(
                res.text,
                final,
                fmt=fmt,
                redact_pii=redact_pii,
                max_chars=max_chars_per_source,
                respect_robots=respect_robots,
            )
            return {"url": final, "ok": True, **fin}
    except Exception as exc2:  # noqa: BLE001
        return {
            "url": url,
            "ok": False,
            "error": str(exc2),
            **({"json": {}} if fmt == "json" else {"markdown": ""}),
        }


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "at-utility-ingest",
        "compliance_enforce": COMPLIANCE_ENFORCE,
        "jurisdiction_profile": JURISDICTION,
        "web_bot_auth": signing_enabled(),
        "pay_per_crawl": "surface_402_no_autopay",
    }


@app.get("/v1/compliance/purposes")
async def list_purposes() -> dict[str, Any]:
    from at_utility.compliance.policy import ALLOWED_PURPOSES, BLOCKED_PURPOSES, PURPOSE_RISK

    return {
        "allowed": sorted(ALLOWED_PURPOSES),
        "blocked": sorted(BLOCKED_PURPOSES),
        "risk_bands": PURPOSE_RISK,
        "notes": "See docs/LEGAL.md - entire ingest path is public-only.",
    }


@app.post("/v1/ingest")
async def ingest(body: IngestRequest) -> dict[str, Any]:
    respect_robots = (
        RESPECT_ROBOTS_DEFAULT if body.respect_robots is None else body.respect_robots
    )
    redact_pii = REDACT_PII_DEFAULT if body.redact_pii is None else body.redact_pii
    jurisdiction = body.jurisdiction_profile or JURISDICTION
    max_chars = (
        MAX_CHARS_PER_SOURCE
        if body.max_chars_per_source is None
        else int(body.max_chars_per_source)
    )

    decision = evaluate_ingest_request(
        purpose=body.purpose,
        urls=body.urls,
        query=body.query,
        compliance_ack=body.compliance_ack,
        enforce=COMPLIANCE_ENFORCE,
        require_ack=COMPLIANCE_ENFORCE,
        jurisdiction_profile=jurisdiction,
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=403,
            detail=ComplianceError(
                "compliance_denied",
                "; ".join(decision.reasons),
                details={
                    "purpose": decision.purpose,
                    "blocked_urls": decision.blocked_urls,
                },
            ).as_http_detail(),
        )

    urls = list(body.urls)
    if body.query and len(urls) < body.max_results:
        found = await meta_search(body.query, max_results=body.max_results)
        for u in found:
            if u not in urls:
                urls.append(u)
            if len(urls) >= body.max_results:
                break

    fmt = (body.format or "markdown").strip().lower()
    if fmt not in ("markdown", "json"):
        fmt = "markdown"

    documents = []
    for u in urls[: body.max_results]:
        documents.append(
            await fetch_url(
                u,
                respect_robots=respect_robots,
                redact_pii=redact_pii,
                max_chars_per_source=max_chars,
                fmt=fmt,
            )
        )
    ok_docs = [d for d in documents if d.get("ok")]
    return {
        "ok": bool(ok_docs),
        "query": body.query,
        "documents": documents,
        "format": fmt,
        "metered_fetches": len(ok_docs),
        "compliance": {
            "purpose": decision.purpose,
            "risk_band": decision.risk_band,
            "warnings": decision.warnings,
            "jurisdiction_profile": decision.jurisdiction_profile,
            "respect_robots": respect_robots,
            "redact_pii": redact_pii,
            "max_chars_per_source": max_chars,
            "framework": "uk_gdpr_cma_us_cfaa_ccpa_public_only_adjacent",
        },
    }


def run() -> None:
    import uvicorn

    port = int(os.getenv("WORKER_PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
