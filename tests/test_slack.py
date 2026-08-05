"""Slack /observer slash command: signature verification, allowlist, and route."""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility import slack
from at_utility.config import get_settings
from at_utility.main import app, state
from tests.app_state import wire_memory_app_state

SECRET = "8f14e45fceea167a5a36dedd4bea2543"


def _sign(secret: str, timestamp: str, body: bytes) -> str:
    base = f"v0:{timestamp}:".encode() + body
    return "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()


# --- pure unit tests (no app) ------------------------------------------------


def test_signature_roundtrip_valid():
    ts = str(int(time.time()))
    body = b"command=%2Fobserver&user_id=U1"
    sig = _sign(SECRET, ts, body)
    assert slack.verify_slack_signature(SECRET, ts, body, sig)


def test_signature_rejects_tampered_body():
    ts = str(int(time.time()))
    sig = _sign(SECRET, ts, b"command=%2Fobserver&user_id=U1")
    assert not slack.verify_slack_signature(SECRET, ts, b"command=%2Fobserver&user_id=EVIL", sig)


def test_signature_rejects_wrong_secret():
    ts = str(int(time.time()))
    body = b"x=1"
    sig = _sign(SECRET, ts, body)
    assert not slack.verify_slack_signature("different-secret", ts, body, sig)


def test_signature_rejects_stale_timestamp():
    ts = str(int(time.time()) - 3600)
    body = b"x=1"
    sig = _sign(SECRET, ts, body)
    assert not slack.verify_slack_signature(SECRET, ts, body, sig)


def test_signature_rejects_missing_inputs():
    assert not slack.verify_slack_signature("", "1", b"x", "v0=abc")
    assert not slack.verify_slack_signature(SECRET, "", b"x", "v0=abc")
    assert not slack.verify_slack_signature(SECRET, "1", b"x", "")
    assert not slack.verify_slack_signature(SECRET, "not-a-number", b"x", "v0=abc")


def test_allowlist_is_fail_closed_when_unset():
    assert not slack.caller_allowed("", "", "Tany", "Uany")


def test_allowlist_enforces_team_and_user():
    assert slack.caller_allowed("T1,T2", "U1", "T2", "U1")
    assert not slack.caller_allowed("T1,T2", "U1", "T9", "U1")
    assert not slack.caller_allowed("T1", "U1,U2", "T1", "U9")


def test_parse_command():
    form = slack.parse_command(b"command=%2Fobserver&user_id=U1&text=run+now")
    assert form["command"] == "/observer"
    assert form["user_id"] == "U1"
    assert form["text"] == "run now"


# --- route tests -------------------------------------------------------------


@pytest.fixture
async def _wired():
    store = await wire_memory_app_state()
    settings = get_settings()
    settings.slack_signing_secret = SECRET
    settings.slack_allow_team_ids = "T123"
    settings.slack_allow_user_ids = "U1"
    settings.cursor_observer_webhook = ""  # trigger is a logged no-op in tests
    state.settings = settings
    yield settings
    await store.close()
    get_settings.cache_clear()


def _post_args(settings, *, user_id="U1", team_id="T123", skew=0):
    body = urllib.parse.urlencode(
        {"command": "/observer", "user_id": user_id, "team_id": team_id, "text": ""}
    ).encode()
    ts = str(int(time.time()) + skew)
    return body, {
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": _sign(settings.slack_signing_secret, ts, body),
        "Content-Type": "application/x-www-form-urlencoded",
    }


@pytest.mark.asyncio
async def test_route_valid_command_acks(_wired):
    body, headers = _post_args(_wired)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/slack/observer", content=body, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["response_type"] == "ephemeral"
    assert "Running the daily sweep" in data["text"]


@pytest.mark.asyncio
async def test_route_bad_signature_401(_wired):
    body, headers = _post_args(_wired)
    headers["X-Slack-Signature"] = "v0=deadbeef"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/slack/observer", content=body, headers=headers)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_route_unlisted_user_denied(_wired):
    body, headers = _post_args(_wired, user_id="U-INTRUDER")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/slack/observer", content=body, headers=headers)
    assert res.status_code == 200
    assert "allowlist" in res.json()["text"]


@pytest.mark.asyncio
async def test_route_cooldown_blocks_second_call(_wired):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        b1, h1 = _post_args(_wired)
        first = await client.post("/v1/slack/observer", content=b1, headers=h1)
        b2, h2 = _post_args(_wired)
        second = await client.post("/v1/slack/observer", content=b2, headers=h2)
    assert "Running the daily sweep" in first.json()["text"]
    assert "before triggering again" in second.json()["text"]


@pytest.mark.asyncio
async def test_route_503_when_unconfigured(_wired):
    _wired.slack_signing_secret = ""
    body, headers = _post_args(_wired)  # signs with empty secret; route 503s first
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/slack/observer", content=body, headers=headers)
    assert res.status_code == 503
