"""Append-only audit log for org / tenant API access and policy decisions."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from at_utility.redis_store import CacheStore


@dataclass
class AuditEntry:
    audit_id: str
    ts: int
    org_id: str
    tenant_id: str
    actor: str
    action: str
    detail: dict[str, Any]
    allowed: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "AuditEntry":
        data = json.loads(raw)
        return AuditEntry(**{k: data[k] for k in AuditEntry.__dataclass_fields__ if k in data})


class AuditLog:
    MAX_ENTRIES = 20_000

    def __init__(self, store: CacheStore):
        self._store = store

    def _key(self, org_id: str, tenant_id: str) -> str:
        scope = org_id if org_id else tenant_id
        return f"at:audit:{scope}:log"

    async def record(
        self,
        *,
        org_id: str = "",
        tenant_id: str = "",
        actor: str = "",
        action: str,
        detail: dict[str, Any] | None = None,
        allowed: bool = True,
    ) -> AuditEntry:
        entry = AuditEntry(
            audit_id=uuid.uuid4().hex,
            ts=int(time.time()),
            org_id=org_id or "",
            tenant_id=tenant_id or "",
            actor=actor or "",
            action=action,
            detail=detail or {},
            allowed=allowed,
        )
        key = self._key(org_id, tenant_id)
        await self._store.list_push(key, entry.to_json())
        length = await self._store.list_len(key)
        if length > self.MAX_ENTRIES and hasattr(self._store, "list_trim"):
            await self._store.list_trim(key, length - self.MAX_ENTRIES, -1)
        return entry

    async def list_entries(
        self,
        *,
        org_id: str = "",
        tenant_id: str = "",
        limit: int = 200,
    ) -> list[AuditEntry]:
        key = self._key(org_id, tenant_id)
        raw_items = await self._store.list_range(key, -max(limit, 50), -1)
        out: list[AuditEntry] = []
        for raw in reversed(raw_items):
            try:
                out.append(AuditEntry.from_json(raw))
            except (ValueError, TypeError, KeyError):
                continue
            if len(out) >= limit:
                break
        return out
