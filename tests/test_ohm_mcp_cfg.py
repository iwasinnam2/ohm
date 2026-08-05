"""MCP client config hardening for directory verification."""

import os

import pytest


def test_rejects_bootstrap_key_on_public_api(monkeypatch):
    monkeypatch.setenv("OHM_API_KEY", "sk-at-dev")
    monkeypatch.setenv("OHM_BASE_URL", "https://api.withohm.dev/v1")
    from ohm_mcp import _cfg

    with pytest.raises(RuntimeError, match="sk-at-dev"):
        _cfg()


def test_allows_bootstrap_on_localhost(monkeypatch):
    monkeypatch.setenv("OHM_API_KEY", "sk-at-dev")
    monkeypatch.setenv("OHM_BASE_URL", "http://127.0.0.1:8081/v1")
    from ohm_mcp import _cfg

    base, key, _ = _cfg()
    assert key == "sk-at-dev"
    assert "8081" in base
