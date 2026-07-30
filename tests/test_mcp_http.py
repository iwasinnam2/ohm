"""Remote (stateless streamable-HTTP) MCP transport tests."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("mcp")

from starlette.testclient import TestClient  # noqa: E402

import ohm_mcp  # noqa: E402


@pytest.fixture(autouse=True)
def _allow_testserver_host(monkeypatch):
    # Starlette TestClient sends Host: testserver; keep DNS-rebinding
    # protection enabled but allow it for the in-process app.
    monkeypatch.setenv("OHM_MCP_ALLOWED_HOSTS", "testserver,localhost")


MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "MCP-Protocol-Version": "2025-06-18",
}


def _rpc(client: TestClient, method: str, params: dict | None = None, id_: int = 1):
    body = {"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}}
    return client.post("/mcp", headers=MCP_HEADERS, json=body)


def _initialize(client: TestClient):
    return _rpc(
        client,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0"},
        },
    )


def test_http_app_stateless_initialize_and_list_tools():
    app = ohm_mcp.http_app()
    with TestClient(app) as client:
        res = _initialize(client)
        assert res.status_code == 200
        init = res.json()
        assert init["result"]["serverInfo"]["name"] == "ohm"

        # Stateless core: a second request needs no session id and no
        # initialize handshake on the same connection.
        res = _rpc(client, "tools/list", id_=2)
        assert res.status_code == 200
        tools = {t["name"] for t in res.json()["result"]["tools"]}
        assert {"ohm_chat", "ohm_fetch_web", "ohm_usage"} <= tools
        # ctx is transport plumbing, not tool surface
        for t in res.json()["result"]["tools"]:
            assert "ctx" not in (t.get("inputSchema", {}).get("properties") or {})


def test_http_tool_call_uses_authorization_passthrough(monkeypatch):
    """Per-request Authorization header reaches the gateway call unchanged."""
    seen: dict = {}

    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "choices": [{"message": {"role": "assistant", "content": "pong"}}]
            }

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, json=None):
            seen["url"] = url
            seen["headers"] = headers or {}
            seen["body"] = json or {}
            return FakeResponse()

    monkeypatch.setattr(ohm_mcp.httpx, "AsyncClient", FakeClient)
    monkeypatch.delenv("OHM_API_KEY", raising=False)
    monkeypatch.setenv("OHM_BASE_URL", "http://gw.test/v1")

    app = ohm_mcp.http_app()
    with TestClient(app) as client:
        _initialize(client)
        res = client.post(
            "/mcp",
            headers={
                **MCP_HEADERS,
                "Authorization": "Bearer sk-at-tenant-123",
                "X-Ohm-Upstream-Key": "sk-upstream-456",
            },
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "ohm_chat",
                    "arguments": {"prompt": "ping", "model": "mock"},
                },
            },
        )
        assert res.status_code == 200
        payload = res.json()
        content = payload["result"]["content"][0]["text"]
        assert content == "pong"

    assert seen["url"] == "http://gw.test/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer sk-at-tenant-123"
    assert seen["headers"]["X-Ohm-Upstream-Key"] == "sk-upstream-456"


def test_http_tool_call_without_key_errors(monkeypatch):
    monkeypatch.delenv("OHM_API_KEY", raising=False)
    monkeypatch.delenv("OHM_UPSTREAM_KEY", raising=False)

    app = ohm_mcp.http_app()
    with TestClient(app) as client:
        _initialize(client)
        res = client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "ohm_usage", "arguments": {}},
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload["result"].get("isError") is True
        text = json.dumps(payload["result"]["content"])
        assert "Authorization" in text or "OHM_API_KEY" in text
