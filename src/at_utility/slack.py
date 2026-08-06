"""Slack slash-command support for the /observer on-demand trigger.

Pure, dependency-light helpers so the security-critical parts — signature
verification and the caller allowlist — are unit-testable without a network or
FastAPI. The route in main.py wires these to the request and the automation
webhook.

Slack signs every request; verify over the RAW body before parsing, because
re-serializing changes the signed bytes. See
https://docs.slack.dev/interactivity/implementing-slash-commands
"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

SIGNATURE_VERSION = "v0"
DEFAULT_MAX_SKEW_SECONDS = 300


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    raw_body: bytes,
    signature: str,
    *,
    now: float | None = None,
    max_skew_seconds: int = DEFAULT_MAX_SKEW_SECONDS,
) -> bool:
    """True only if the signature matches and the timestamp is fresh.

    Fresh-timestamp check is the replay guard; the constant-time compare avoids
    leaking match progress. Any missing input is a hard False, never an
    exception the caller has to remember to catch.
    """
    if not signing_secret or not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = time.time() if now is None else now
    if abs(current - ts) > max_skew_seconds:
        return False
    base = b"%s:%s:%s" % (SIGNATURE_VERSION.encode(), timestamp.encode(), raw_body)
    digest = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
    expected = f"{SIGNATURE_VERSION}={digest}"
    return hmac.compare_digest(expected, signature)


def parse_command(raw_body: bytes) -> dict[str, str]:
    """Slash commands arrive as application/x-www-form-urlencoded."""
    decoded = raw_body.decode("utf-8", errors="replace")
    return {k: v[0] for k, v in urllib.parse.parse_qs(decoded).items() if v}


def _split(raw: str) -> set[str]:
    return {item.strip() for item in (raw or "").split(",") if item.strip()}


def caller_allowed(
    allow_team_ids: str,
    allow_user_ids: str,
    team_id: str,
    user_id: str,
) -> bool:
    """Fail-closed allowlist.

    A valid signature only proves Slack relayed the request, not that the sender
    may spend money — each invocation starts a billable run. So: if no allowlist
    is configured at all, deny (never wide open); if a list is configured, the
    caller must be on every configured list.
    """
    teams = _split(allow_team_ids)
    users = _split(allow_user_ids)
    if not teams and not users:
        return False
    if teams and team_id not in teams:
        return False
    if users and user_id not in users:
        return False
    return True
