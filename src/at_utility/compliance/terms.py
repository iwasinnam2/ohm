"""Terms of Service / DPA acknowledgement gates."""

from __future__ import annotations

from typing import Any, Optional

from at_utility.compliance.policy import ComplianceError

DEFAULT_TERMS_VERSION = "tos-2026-07-26"
DEFAULT_DPA_VERSION = "dpa-2026-07-26"


def require_terms_acks(
    *,
    terms_ack: bool,
    dpa_ack: bool,
    enforce: bool = True,
    require: bool = True,
) -> None:
    """Raise ComplianceError when required acks are missing."""
    if not enforce or not require:
        return
    missing: list[str] = []
    if not terms_ack:
        missing.append("terms_ack")
    if not dpa_ack:
        missing.append("dpa_ack")
    if missing:
        raise ComplianceError(
            "terms_ack_required",
            "Web context requires acknowledgement of Terms and DPA: "
            + ", ".join(missing)
            + " must be true (see docs/legal/).",
            details={"missing": missing},
        )


def assert_cache_training_denied(allow_cache_training: bool) -> None:
    """Hard-deny any attempt to enable cache→training export paths."""
    if allow_cache_training:
        raise ComplianceError(
            "cache_training_forbidden",
            "AT_COMPLIANCE_ALLOW_CACHE_TRAINING must remain false; "
            "Redis cache is identical-request replay only, not a training corpus.",
        )


def terms_metadata(
    *,
    terms_version: str,
    dpa_version: str,
    require_terms_ack: bool,
    public_base: str = "https://api.withohm.dev",
) -> dict[str, Any]:
    """Public URLs for MVP docs host; repo paths retained for operators."""
    base = public_base.rstrip("/")
    return {
        "terms_version": terms_version,
        "dpa_version": dpa_version,
        "require_terms_ack": require_terms_ack,
        "documents": {
            "terms": f"{base}/docs/terms",
            "privacy": f"{base}/docs/privacy",
            "dpa": f"{base}/docs/dpa",
            "legal": f"{base}/docs/legal",
            "security": f"{base}/docs/security",
        },
        "templates": {
            "terms": "docs/legal/TERMS_OF_SERVICE.md",
            "dpa": "docs/legal/DPA.md",
            "privacy": "docs/legal/PRIVACY.md",
            "upstream": "docs/legal/UPSTREAM_PROVIDERS.md",
        },
        "key_prefix": "sk-at",
        "key_prefix_note": "Legacy prefix; product brand is Ohm. sk-ohm cutover deferred.",
        "header_prefix": "X-AT-",
    }
