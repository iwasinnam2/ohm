"""Purpose + risk matrix for web ingestion (UK GDPR / CMA + US CFAA / CCPA)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IngestPurpose(str, Enum):
    """Allowed product purposes — mapped to the repo risk matrix."""

    PUBLIC_WEB_RETRIEVAL = "public_web_retrieval"  # AI-search style: cite public pages
    BUSINESS_CATALOG = "business_catalog"  # prices, SKUs, product specs
    PUBLIC_COMPANY_INFO = "public_company_info"  # public about/contact pages (org-level)
    JOB_LISTINGS = "job_listings"  # public job ads (not CVs / applicants)


ALLOWED_PURPOSES: frozenset[str] = frozenset(p.value for p in IngestPurpose)

# Explicitly rejected — High/Severe cells on the risk matrix
BLOCKED_PURPOSES: frozenset[str] = frozenset(
    {
        "lead_generation",
        "contact_harvest",
        "person_dossier",
        "people_search",
        "biometric",
        "face_match",
        "login_gated",
        "private_account",
        "credential_reuse",
        "social_profile_bulk",
        # PECR / anti-spam adjacent
        "cold_email",
        "sms_blast",
        "direct_marketing_list",
        "mailing_list_build",
    }
)

# Purpose → default risk band (documentation / API metadata)
PURPOSE_RISK: dict[str, str] = {
    IngestPurpose.PUBLIC_WEB_RETRIEVAL.value: "medium",
    IngestPurpose.BUSINESS_CATALOG.value: "low",
    IngestPurpose.PUBLIC_COMPANY_INFO.value: "low_medium",
    IngestPurpose.JOB_LISTINGS.value: "low",
}


class ComplianceError(ValueError):
    """Raised when a request violates the legal operating bounds."""

    def __init__(self, code: str, message: str, *, details: Optional[dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def as_http_detail(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


@dataclass
class ComplianceDecision:
    allowed: bool
    purpose: str
    risk_band: str
    reasons: list[str] = field(default_factory=list)
    blocked_urls: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pii_redaction: bool = True
    jurisdiction_profile: str = "uk_us"

    def raise_if_denied(self) -> None:
        if not self.allowed:
            raise ComplianceError(
                "compliance_denied",
                "; ".join(self.reasons) or "Request denied by compliance policy",
                details={
                    "purpose": self.purpose,
                    "blocked_urls": self.blocked_urls,
                    "warnings": self.warnings,
                },
            )


def require_purpose(raw: Optional[str], *, enforce: bool = True) -> str:
    """Normalize and validate purpose. When enforce=False, default to public retrieval."""
    if not raw or not str(raw).strip():
        if enforce:
            raise ComplianceError(
                "purpose_required",
                "web_purpose is required when fetch_web_context is enabled. "
                f"Allowed: {sorted(ALLOWED_PURPOSES)}",
            )
        return IngestPurpose.PUBLIC_WEB_RETRIEVAL.value

    purpose = str(raw).strip().lower()
    if purpose in BLOCKED_PURPOSES:
        raise ComplianceError(
            "purpose_blocked",
            f"Purpose '{purpose}' is prohibited (High/Severe risk under UK/US online-data rules).",
            details={"blocked_purposes": sorted(BLOCKED_PURPOSES)},
        )
    if purpose not in ALLOWED_PURPOSES:
        raise ComplianceError(
            "purpose_invalid",
            f"Unknown purpose '{purpose}'. Allowed: {sorted(ALLOWED_PURPOSES)}",
        )
    return purpose


def evaluate_ingest_request(
    *,
    purpose: Optional[str],
    urls: Optional[list[str]],
    query: Optional[str],
    compliance_ack: bool,
    enforce: bool = True,
    require_ack: bool = True,
    jurisdiction_profile: str = "uk_us",
) -> ComplianceDecision:
    """Gate an ingest request before any network fetch."""
    from at_utility.compliance.url_gate import gate_url

    reasons: list[str] = []
    warnings: list[str] = []
    blocked_urls: list[str] = []

    if not enforce:
        return ComplianceDecision(
            allowed=True,
            purpose=purpose or IngestPurpose.PUBLIC_WEB_RETRIEVAL.value,
            risk_band="unenforced",
            warnings=["Compliance enforcement disabled (dev only)"],
            pii_redaction=False,
            jurisdiction_profile=jurisdiction_profile,
        )

    try:
        normalized = require_purpose(purpose, enforce=True)
    except ComplianceError as exc:
        return ComplianceDecision(
            allowed=False,
            purpose=str(purpose or ""),
            risk_band="denied",
            reasons=[exc.message],
            jurisdiction_profile=jurisdiction_profile,
        )

    if require_ack and not compliance_ack:
        return ComplianceDecision(
            allowed=False,
            purpose=normalized,
            risk_band=PURPOSE_RISK.get(normalized, "medium"),
            reasons=[
                "web_compliance_ack must be true: you confirm public-only retrieval, "
                "no login/credential bypass, no lead harvesting or person dossiers, "
                "and lawful use under UK GDPR/CMA and US CFAA/CCPA where applicable."
            ],
            jurisdiction_profile=jurisdiction_profile,
        )

    url_list = list(urls or [])
    if not url_list and not (query and query.strip()):
        reasons.append("Provide web_query and/or web_urls for public retrieval")

    for u in url_list:
        result = gate_url(u)
        if not result.allowed:
            blocked_urls.append(u)
            reasons.append(f"URL blocked ({result.code}): {u} — {result.reason}")

    # Query heuristics: reject explicit lead-harvest / dossier intent in the query string
    q = (query or "").lower()
    banned_query_fragments = (
        "email list",
        "phone list",
        "scrape contacts",
        "harvest emails",
        "find personal phone",
        "dox ",
        "face recognition",
        "biometric",
        "login password",
        "session token",
        "email these people",
        "build mailing list",
        "cold email",
        "sms blast",
        "spam list",
        "direct marketing list",
    )
    if any(frag in q for frag in banned_query_fragments):
        reasons.append(
            "web_query indicates prohibited activity "
            "(contact harvest, dossier, biometric, credential access, or PECR direct marketing)"
        )

    if jurisdiction_profile in ("uk", "uk_us", "both"):
        warnings.append(
            "UK profile: identifiable people data remains personal data even if public; "
            "outputs are minimised and must not be used for direct marketing without a lawful basis."
        )
    if jurisdiction_profile in ("us", "us_ca", "uk_us", "both"):
        warnings.append(
            "US/CA profile: public pages only; do not continue after access revocation or tech blocks; "
            "CCPA publicly-available carve-outs do not authorize gated access."
        )

    allowed = not reasons
    return ComplianceDecision(
        allowed=allowed,
        purpose=normalized,
        risk_band=PURPOSE_RISK.get(normalized, "medium"),
        reasons=reasons,
        blocked_urls=blocked_urls,
        warnings=warnings,
        pii_redaction=True,
        jurisdiction_profile=jurisdiction_profile,
    )
