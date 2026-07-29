"""Personal-data minimisation for ingested public pages (UK GDPR-minded defaults)."""

from __future__ import annotations

import re
from dataclasses import dataclass


# Practical redaction — not a guarantee of perfect PII detection
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{3,4}(?!\w)"
)
_SSN_ISH_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_ISH_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


@dataclass
class RedactionResult:
    text: str
    email_count: int = 0
    phone_count: int = 0
    other_count: int = 0

    @property
    def total(self) -> int:
        return self.email_count + self.phone_count + self.other_count


def redact_personal_data(text: str, *, enabled: bool = True) -> RedactionResult:
    """Strip common personal identifiers from fetched markdown.

    Default-on for all jurisdictions in this repo: UK treats public identifiable
    data as personal data; CA public carve-outs do not justify shipping emails/phones
    in search-context payloads for lead gen.
    """
    if not enabled or not text:
        return RedactionResult(text=text or "")

    email_count = 0
    phone_count = 0
    other_count = 0

    def _email(m: re.Match[str]) -> str:
        nonlocal email_count
        email_count += 1
        return "[REDACTED_EMAIL]"

    def _phone(m: re.Match[str]) -> str:
        nonlocal phone_count
        # Avoid redacting years / short numbers / product SKUs-like sequences
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) < 10:
            return m.group(0)
        phone_count += 1
        return "[REDACTED_PHONE]"

    def _other(m: re.Match[str]) -> str:
        nonlocal other_count
        other_count += 1
        return "[REDACTED_ID]"

    out = _EMAIL_RE.sub(_email, text)
    out = _SSN_ISH_RE.sub(_other, out)
    out = _CC_ISH_RE.sub(_other, out)
    out = _PHONE_RE.sub(_phone, out)
    return RedactionResult(
        text=out,
        email_count=email_count,
        phone_count=phone_count,
        other_count=other_count,
    )
