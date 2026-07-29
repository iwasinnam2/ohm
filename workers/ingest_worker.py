"""Playwright + meta-search ingestion worker (public-only, compliance-gated)."""

from __future__ import annotations

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


async def meta_search(query: str, max_results: int = 3) -> list[str]:
    """Lightweight DuckDuckGo HTML meta-search (no owned index)."""
    if SERP_PROVIDER != "duckduckgo":
        log.warning("serp provider %s not implemented; using duckduckgo", SERP_PROVIDER)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        res = await client.get(url, headers={"User-Agent": BOT_UA})
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


async def fetch_url(
    url: str,
    *,
    respect_robots: bool,
    redact_pii: bool,
    max_chars_per_source: int,
) -> dict[str, Any]:
    """Prefer Playwright; fall back to httpx if browser not installed."""
    g = gate_url(url)
    if not g.allowed:
        return {
            "url": url,
            "markdown": "",
            "ok": False,
            "error": g.reason,
            "compliance": {"code": g.code, "allowed": False},
        }

    if not await allowed_by_robots(url, enabled=respect_robots):
        return {
            "url": url,
            "markdown": "",
            "ok": False,
            "error": "Disallowed by robots.txt for OhmBot",
            "compliance": {"code": "robots_disallow", "allowed": False},
        }

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=BOT_UA)
            await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
            # Refuse if navigation landed on an obvious login wall URL
            final = page.url
            final_gate = gate_url(final)
            if not final_gate.allowed:
                await browser.close()
                return {
                    "url": url,
                    "markdown": "",
                    "ok": False,
                    "error": f"Navigation landed on blocked surface: {final_gate.reason}",
                    "compliance": {"code": final_gate.code, "allowed": False, "final_url": final},
                }
            html = await page.content()
            await browser.close()
            md = html_to_markdown(html, final)
            fin = _finalize_markdown(
                md,
                redact_pii=redact_pii,
                max_chars=max_chars_per_source,
                respect_robots=respect_robots,
            )
            return {"url": final, "ok": True, **fin}
    except Exception as exc:  # noqa: BLE001
        log.info("playwright unavailable or failed (%s); httpx fallback", exc)
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT_MS / 1000.0, follow_redirects=True
            ) as client:
                res = await client.get(url, headers={"User-Agent": BOT_UA})
                res.raise_for_status()
                final = str(res.url)
                final_gate = gate_url(final)
                if not final_gate.allowed:
                    return {
                        "url": url,
                        "markdown": "",
                        "ok": False,
                        "error": f"Redirected to blocked surface: {final_gate.reason}",
                        "compliance": {
                            "code": final_gate.code,
                            "allowed": False,
                            "final_url": final,
                        },
                    }
                md = html_to_markdown(res.text, final)
                fin = _finalize_markdown(
                    md,
                    redact_pii=redact_pii,
                    max_chars=max_chars_per_source,
                    respect_robots=respect_robots,
                )
                return {"url": final, "ok": True, **fin}
        except Exception as exc2:  # noqa: BLE001
            return {"url": url, "markdown": "", "ok": False, "error": str(exc2)}


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "at-utility-ingest",
        "compliance_enforce": COMPLIANCE_ENFORCE,
        "jurisdiction_profile": JURISDICTION,
    }


@app.get("/v1/compliance/purposes")
async def list_purposes() -> dict[str, Any]:
    from at_utility.compliance.policy import ALLOWED_PURPOSES, BLOCKED_PURPOSES, PURPOSE_RISK

    return {
        "allowed": sorted(ALLOWED_PURPOSES),
        "blocked": sorted(BLOCKED_PURPOSES),
        "risk_bands": PURPOSE_RISK,
        "notes": "See docs/LEGAL.md — entire ingest path is public-only.",
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

    documents = []
    for u in urls[: body.max_results]:
        documents.append(
            await fetch_url(
                u,
                respect_robots=respect_robots,
                redact_pii=redact_pii,
                max_chars_per_source=max_chars,
            )
        )
    ok_docs = [d for d in documents if d.get("ok")]
    return {
        "ok": bool(ok_docs),
        "query": body.query,
        "documents": documents,
        "format": body.format,
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
