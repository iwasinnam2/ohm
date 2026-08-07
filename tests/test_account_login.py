"""Tenant email/password login restores Intermediate bearer."""

import pytest

from at_utility.config import Settings
from at_utility.redis_store import MemoryStore
from at_utility.tenants import TenantRegistry


@pytest.mark.asyncio
async def test_issue_with_password_and_login():
    store = MemoryStore()
    settings = Settings(at_account_secret="test-account-secret")
    tenants = TenantRegistry(store, settings)
    raw, record = await tenants.issue(
        plan="payg",
        email="Ada@Example.com",
        password="correct-horse",
        label="Ada",
    )
    assert raw.startswith("sk-at-")
    assert record.email == "ada@example.com"
    assert record.password_hash
    assert record.api_key_wrapped
    profile = await store.get(f"at:global:apikey:{record.key_hash}:profile")
    assert profile and "ada@example.com" in profile

    ok = await tenants.login_with_password("ada@example.com", "correct-horse")
    assert ok is not None
    restored, rec2 = ok
    assert restored == raw
    assert rec2.tenant_id == record.tenant_id

    assert await tenants.login_with_password("ada@example.com", "nope") is None
