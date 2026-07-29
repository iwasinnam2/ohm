"""Legal-compliance controls for Ohm / at-utility web ingestion.

Enforces the UK/US online-data framework plus adjacent terms/DPA,
copyright excerpts, and PECR gates — see docs/LEGAL.md.
"""

from at_utility.compliance.copyright import apply_excerpt_cap, cap_total_context
from at_utility.compliance.pii import redact_personal_data
from at_utility.compliance.policy import (
    ALLOWED_PURPOSES,
    BLOCKED_PURPOSES,
    ComplianceDecision,
    ComplianceError,
    IngestPurpose,
    evaluate_ingest_request,
    require_purpose,
)
from at_utility.compliance.terms import (
    assert_cache_training_denied,
    require_terms_acks,
    terms_metadata,
)
from at_utility.compliance.url_gate import UrlGateResult, gate_url

__all__ = [
    "ALLOWED_PURPOSES",
    "BLOCKED_PURPOSES",
    "ComplianceDecision",
    "ComplianceError",
    "IngestPurpose",
    "UrlGateResult",
    "apply_excerpt_cap",
    "assert_cache_training_denied",
    "cap_total_context",
    "evaluate_ingest_request",
    "gate_url",
    "redact_personal_data",
    "require_purpose",
    "require_terms_acks",
    "terms_metadata",
]
