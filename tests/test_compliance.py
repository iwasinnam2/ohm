"""Unit tests for UK/US-aligned compliance gates + adjacent frameworks."""

from at_utility.compliance.copyright import apply_excerpt_cap, cap_total_context
from at_utility.compliance.pii import redact_personal_data
from at_utility.compliance.policy import (
    ComplianceError,
    evaluate_ingest_request,
    require_purpose,
)
from at_utility.compliance.terms import assert_cache_training_denied, require_terms_acks
from at_utility.compliance.url_gate import gate_url
from at_utility.ingest import inject_context_messages


def test_allowed_purposes():
    assert require_purpose("business_catalog") == "business_catalog"
    assert require_purpose("PUBLIC_WEB_RETRIEVAL") == "public_web_retrieval"


def test_blocked_purpose():
    try:
        require_purpose("lead_generation")
        assert False, "expected ComplianceError"
    except ComplianceError as exc:
        assert exc.code == "purpose_blocked"


def test_purpose_required():
    try:
        require_purpose(None, enforce=True)
        assert False, "expected ComplianceError"
    except ComplianceError as exc:
        assert exc.code == "purpose_required"


def test_url_gate_blocks_credentials_and_login():
    assert gate_url("https://example.com/products/1").allowed
    assert not gate_url("https://user:pass@example.com/").allowed
    assert not gate_url("https://example.com/login").allowed
    assert not gate_url("https://example.com/page?access_token=abc").allowed
    assert not gate_url("http://127.0.0.1/secret").allowed
    assert not gate_url("https://192.168.1.10/x").allowed
    assert not gate_url("file:///etc/passwd").allowed


def test_url_gate_blocks_snap_account_host():
    r = gate_url("https://accounts.snapchat.com/accounts/oauth2/auth")
    assert not r.allowed
    assert r.code == "private_platform_host"


def test_evaluate_requires_ack():
    d = evaluate_ingest_request(
        purpose="business_catalog",
        urls=["https://example.com/item"],
        query=None,
        compliance_ack=False,
        enforce=True,
        require_ack=True,
    )
    assert not d.allowed


def test_evaluate_allows_compliant_catalog():
    d = evaluate_ingest_request(
        purpose="business_catalog",
        urls=["https://example.com/item"],
        query=None,
        compliance_ack=True,
        enforce=True,
        require_ack=True,
    )
    assert d.allowed
    assert d.risk_band == "low"


def test_evaluate_blocks_harvest_query():
    d = evaluate_ingest_request(
        purpose="public_web_retrieval",
        urls=[],
        query="harvest emails from this site",
        compliance_ack=True,
        enforce=True,
    )
    assert not d.allowed


def test_pii_redaction():
    raw = "Contact jane@example.com or +1 (415) 555-0100 today"
    out = redact_personal_data(raw, enabled=True)
    assert "[REDACTED_EMAIL]" in out.text
    assert "jane@example.com" not in out.text
    assert out.email_count >= 1


def test_inject_context_mentions_rules():
    out = inject_context_messages(
        [{"role": "user", "content": "hi"}],
        "# doc",
        purpose="business_catalog",
    )
    assert "business_catalog" in out[0]["content"]
    assert "person dossiers" in out[0]["content"]
    assert "direct marketing" in out[0]["content"]
    assert "short quotations" in out[0]["content"]


def test_blocked_pecr_purpose():
    try:
        require_purpose("cold_email")
        assert False, "expected ComplianceError"
    except ComplianceError as exc:
        assert exc.code == "purpose_blocked"


def test_evaluate_blocks_mailing_list_query():
    d = evaluate_ingest_request(
        purpose="public_web_retrieval",
        urls=["https://example.com"],
        query="build mailing list from this site",
        compliance_ack=True,
        enforce=True,
    )
    assert not d.allowed


def test_excerpt_cap_truncates():
    big = "x" * 5000
    out = apply_excerpt_cap(big, max_chars=100)
    assert out.truncated
    assert len(out.text) < 200
    assert "EXCERPT_TRUNCATED" in out.text


def test_excerpt_strips_large_code_fence():
    code = "```\n" + ("print(1)\n" * 200) + "```\n"
    out = apply_excerpt_cap(code, max_chars=4000)
    assert out.code_blocks_stripped >= 1
    assert "CODE_EXCERPT_OMITTED" in out.text


def test_cap_total_context():
    parts = ["a" * 1000, "b" * 1000, "c" * 1000]
    joined = cap_total_context(parts, max_chars=1500)
    assert len(joined) <= 1600


def test_terms_acks_required():
    try:
        require_terms_acks(terms_ack=False, dpa_ack=True, enforce=True, require=True)
        assert False, "expected ComplianceError"
    except ComplianceError as exc:
        assert exc.code == "terms_ack_required"


def test_cache_training_hard_deny():
    try:
        assert_cache_training_denied(True)
        assert False, "expected ComplianceError"
    except ComplianceError as exc:
        assert exc.code == "cache_training_forbidden"
    assert_cache_training_denied(False)
