"""Waste-check demo contract: shared public key must never demo as HIT→HIT.

The /demo Prove button uses one public OHM_DEMO_API_KEY for all visitors.
A fixed prompt warms the cache on the first run; every later visitor would see
HIT→HIT and the Pro+ narrative dies. Each Prove must mint a fresh nonce and
send that same prompt twice → MISS then HIT.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from at_utility.config import get_settings
from at_utility.main import app
from tests.app_state import wire_memory_app_state


HEADERS = {"Authorization": "Bearer sk-at-dev"}


@pytest.fixture(autouse=True)
async def _mem_state():
    store = await wire_memory_app_state()
    yield
    await store.close()
    get_settings.cache_clear()


def _payload(prompt: str) -> dict:
    return {
        "model": "mock",
        "messages": [{"role": "user", "content": prompt}],
        "ohm_path": "self-proof",
    }


def fresh_proof_prompt() -> str:
    """Mirror site/src/components/WasteCheckClient.tsx::freshProofPrompt."""
    return f"ohm-self-proof {uuid.uuid4()}"


@pytest.mark.asyncio
async def test_fixed_prompt_on_shared_key_goes_hit_hit_after_warmup():
    """Documents the failure mode the demo must not ship."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fixed = "ohm-self-proof-v1-regression"
        miss = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload(fixed)
        )
        assert miss.status_code == 200
        assert miss.headers.get("x-at-cache") == "MISS"
        hit = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload(fixed)
        )
        assert hit.headers.get("x-at-cache") == "HIT"
        # "Second visitor" with the same fixed prompt — both HITs
        a = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload(fixed)
        )
        b = await client.post(
            "/v1/chat/completions", headers=HEADERS, json=_payload(fixed)
        )
        assert a.headers.get("x-at-cache") == "HIT"
        assert b.headers.get("x-at-cache") == "HIT"


@pytest.mark.asyncio
async def test_unique_prompt_per_prove_always_miss_then_hit():
    """What WasteCheckClient must do on every Prove click."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(3):
            prompt = fresh_proof_prompt()
            first = await client.post(
                "/v1/chat/completions", headers=HEADERS, json=_payload(prompt)
            )
            second = await client.post(
                "/v1/chat/completions", headers=HEADERS, json=_payload(prompt)
            )
            assert first.status_code == 200
            assert second.status_code == 200
            assert first.headers.get("x-at-cache") == "MISS"
            assert second.headers.get("x-at-cache") == "HIT"


@pytest.mark.asyncio
async def test_fresh_proof_prompts_are_unique():
    prompts = {fresh_proof_prompt() for _ in range(50)}
    assert len(prompts) == 50
    assert all(p.startswith("ohm-self-proof ") for p in prompts)
