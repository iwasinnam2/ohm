"""Self-serve checkout: pending signup → issue key after Stripe completes."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from at_utility.config import Settings
from at_utility.redis_store import CacheStore
from at_utility.tenants import TenantRecord, TenantRegistry

log = logging.getLogger("at_utility.checkout")

PENDING_TTL_SECONDS = 86_400
REVEAL_TTL_SECONDS = 3_600


def _pending_key(pending_id: str) -> str:
    return f"at:global:checkout_pending:{pending_id}"


def _reveal_key(session_id: str) -> str:
    return f"at:global:checkout_reveal:{session_id}"


def _session_tenant_key(session_id: str) -> str:
    return f"at:global:checkout_session:{session_id}"


def new_pending_id() -> str:
    return f"pend_{uuid.uuid4().hex[:16]}"


async def save_pending(
    store: CacheStore, pending_id: str, payload: dict[str, Any]
) -> None:
    await store.set(
        _pending_key(pending_id),
        json.dumps(payload),
        ttl_seconds=PENDING_TTL_SECONDS,
    )


async def load_pending(
    store: CacheStore, pending_id: str
) -> Optional[dict[str, Any]]:
    if not pending_id:
        return None
    raw = await store.get(_pending_key(pending_id))
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


async def delete_pending(store: CacheStore, pending_id: str) -> None:
    if pending_id:
        await store.delete(_pending_key(pending_id))


async def save_reveal(store: CacheStore, session_id: str, raw_key: str) -> None:
    await store.set(
        _reveal_key(session_id), raw_key, ttl_seconds=REVEAL_TTL_SECONDS
    )


async def take_reveal(store: CacheStore, session_id: str) -> Optional[str]:
    """One-time read of the issued secret for a Checkout session."""
    if not session_id:
        return None
    key = _reveal_key(session_id)
    raw = await store.get(key)
    if raw:
        await store.delete(key)
    return raw


async def bind_session_tenant(
    store: CacheStore, session_id: str, tenant_id: str
) -> None:
    await store.set(_session_tenant_key(session_id), tenant_id, ttl_seconds=0)


async def session_tenant_id(store: CacheStore, session_id: str) -> Optional[str]:
    if not session_id:
        return None
    return await store.get(_session_tenant_key(session_id))


async def fulfill_pending_checkout(
    *,
    store: CacheStore,
    tenants: TenantRegistry,
    settings: Settings,
    session_id: str,
    pending_id: str,
    customer_id: str = "",
    subscription_id: str = "",
) -> tuple[str, TenantRecord] | None:
    """Issue the seat key for a completed Checkout. Idempotent per session.

    Returns ``(raw_key, record)`` when a new reveal is available, or
    ``None`` when the session was already fulfilled and the one-time
    reveal was consumed/expired.
    """
    if not session_id or not pending_id:
        return None

    existing_tid = await session_tenant_id(store, session_id)
    if existing_tid:
        leftover = await store.get(_reveal_key(session_id))
        if leftover:
            await store.delete(_reveal_key(session_id))
            record = await tenants.get(existing_tid)
            if record:
                return leftover, record
        return None

    pending = await load_pending(store, pending_id)
    if not pending:
        return None

    plan = str(pending.get("plan") or "payg")
    raw_key, record = await tenants.issue(
        plan=plan if plan in ("payg", "enterprise") else "payg",
        label=str(pending.get("label") or pending.get("email") or "self-serve"),
        terms_version=str(pending.get("terms_version") or ""),
        dpa_version=str(pending.get("dpa_version") or ""),
    )
    await tenants.attach_stripe(
        record.tenant_id,
        customer_id=customer_id or "",
        subscription_id=subscription_id or "",
        plan=plan if plan in ("payg", "enterprise") else None,
        status="active",
        # $0 Intermediate often settles immediately; invoice.paid also sets this.
        billing_paid=True,
    )
    record = await tenants.get(record.tenant_id) or record
    await bind_session_tenant(store, session_id, record.tenant_id)
    await save_reveal(store, session_id, raw_key)
    await delete_pending(store, pending_id)
    log.info(
        "checkout fulfilled session=%s pending=%s tenant=%s",
        session_id,
        pending_id,
        record.tenant_id,
    )
    return raw_key, record
