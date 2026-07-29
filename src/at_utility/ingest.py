"""Web context ingestion client (talks to Playwright worker) with compliance gates."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from at_utility.compliance import (
    ComplianceError,
    apply_excerpt_cap,
    cap_total_context,
    evaluate_ingest_request,
    require_terms_acks,
)
from at_utility.config import Settings

log = logging.getLogger("at_utility.ingest")


async def fetch_web_context(
    settings: Settings,
    *,
    query: Optional[str] = None,
    urls: Optional[list[str]] = None,
    purpose: Optional[str] = None,
    compliance_ack: bool = False,
    terms_ack: bool = False,
    dpa_ack: bool = False,
    format: str = "markdown",
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Call ingest worker after evaluating the legal policy gate."""
    fmt = (format or "markdown").strip().lower()
    if fmt not in ("markdown", "json"):
        fmt = "markdown"

    try:
        require_terms_acks(
            terms_ack=terms_ack,
            dpa_ack=dpa_ack,
            enforce=settings.at_compliance_enforce,
            require=settings.at_compliance_require_terms_ack,
        )
    except ComplianceError as exc:
        log.warning("ingest terms denied: %s", exc.message)
        return {
            "ok": False,
            "error": exc.message,
            "compliance": exc.as_http_detail(),
            "documents": [],
        }

    decision = evaluate_ingest_request(
        purpose=purpose,
        urls=urls,
        query=query,
        compliance_ack=compliance_ack,
        enforce=settings.at_compliance_enforce,
        require_ack=settings.at_compliance_require_ack,
        jurisdiction_profile=settings.at_compliance_jurisdiction,
    )
    try:
        decision.raise_if_denied()
    except ComplianceError as exc:
        log.warning("ingest compliance denied: %s", exc.message)
        return {
            "ok": False,
            "error": exc.message,
            "compliance": exc.as_http_detail(),
            "documents": [],
        }

    owns = client is None
    client = client or httpx.AsyncClient(timeout=settings.playwright_timeout_ms / 1000.0)
    try:
        res = await client.post(
            f"{settings.ingest_worker_url.rstrip('/')}/v1/ingest",
            json={
                "query": query,
                "urls": urls or [],
                "format": fmt,
                "purpose": decision.purpose,
                "compliance_ack": True,
                "respect_robots": settings.at_compliance_respect_robots,
                "redact_pii": settings.at_compliance_redact_pii,
                "jurisdiction_profile": settings.at_compliance_jurisdiction,
                "max_chars_per_source": settings.at_compliance_max_chars_per_source,
            },
        )
        res.raise_for_status()
        payload = res.json()
        # Defense in depth: re-cap total context client-side
        docs = payload.get("documents") or []
        parts: list[str] = []
        for d in docs:
            if not d.get("ok"):
                continue
            if fmt == "json":
                raw = d.get("json")
                if raw is None:
                    continue
                text = (
                    json.dumps(raw, ensure_ascii=False)
                    if not isinstance(raw, str)
                    else raw
                )
                capped = apply_excerpt_cap(
                    text, max_chars=settings.at_compliance_max_chars_per_source
                )
                d["markdown"] = capped.text
                d.setdefault("compliance", {})["excerpt"] = {
                    "truncated": capped.truncated,
                    "chars_after": capped.chars_after,
                }
                parts.append(
                    f"### {d.get('url', 'source')}\n```json\n{capped.text}\n```"
                )
            else:
                md = d.get("markdown") or ""
                capped = apply_excerpt_cap(
                    md, max_chars=settings.at_compliance_max_chars_per_source
                )
                d["markdown"] = capped.text
                d.setdefault("compliance", {})["excerpt"] = {
                    "truncated": capped.truncated,
                    "chars_after": capped.chars_after,
                }
                parts.append(f"### {d.get('url', 'source')}\n{capped.text}")
        payload["_joined_markdown"] = cap_total_context(
            parts, max_chars=settings.at_compliance_max_context_chars
        )
        payload["format"] = fmt
        payload.setdefault(
            "compliance",
            {
                "purpose": decision.purpose,
                "risk_band": decision.risk_band,
                "warnings": decision.warnings,
                "jurisdiction_profile": decision.jurisdiction_profile,
            },
        )
        return payload
    except Exception as exc:  # noqa: BLE001
        log.warning("ingest failed: %s", exc)
        return {"ok": False, "error": str(exc), "documents": []}
    finally:
        if owns:
            await client.aclose()


def inject_context_messages(
    messages: list[dict[str, Any]],
    context_markdown: str,
    *,
    purpose: str = "public_web_retrieval",
) -> list[dict[str, Any]]:
    system = {
        "role": "system",
        "content": (
            "You are given short PUBLIC web excerpts in markdown for retrieval-augmented answering. "
            f"Ingest purpose: {purpose}. "
            "Rules: (1) Prefer cited public sources when answering. "
            "(2) Treat context as short quotations only — do not reproduce long copyrighted passages. "
            "(3) Do not invent private account details, credentials, or non-public facts. "
            "(4) Do not turn context into contact/lead lists, mailing lists, or person dossiers. "
            "(5) Do not use this context for unsolicited direct marketing. "
            "(6) If personal identifiers were redacted, do not attempt to recover them. "
            "(7) Quote sparingly; attribute with source URLs.\n\n"
            f"--- WEB CONTEXT (short excerpts) ---\n{context_markdown}\n--- END ---"
        ),
    }
    return [system, *messages]
