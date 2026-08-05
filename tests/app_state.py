"""Shared AppState wiring for gateway tests."""

from __future__ import annotations

from at_utility.config import get_settings
from at_utility.providers import MockProvider
from at_utility.redis_store import MemoryStore
import at_utility.main as main_mod


async def wire_memory_app_state(*, clear_stripe: bool = False):
    """Memory store + full runtime bind (tenants + org/ledger/SSO)."""
    get_settings.cache_clear()
    store = MemoryStore()
    settings = get_settings()
    if clear_stripe:
        settings.stripe_secret_key = ""
    main_mod.bind_runtime(
        main_mod.state,
        store,
        settings,
        mock=MockProvider(),
        openai=None,
        anthropic=None,
    )
    return store
