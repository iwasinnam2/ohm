"""Cache tree registry + COW index helpers (Phases 1–2).

Trees are tenant-scoped named namespaces over exact-replay digests.
Default ``main`` keeps v2 keys; named trees use v3. COW read walks parent
chain (depth cap 8). Promote merges child digests into parent index and
copies blob keys.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Optional

from at_utility.cache import DEFAULT_CACHE_TREE, resolve_cache_tree
from at_utility.redis_store import CacheStore

COW_DEPTH_CAP = 8
_META_PREFIX = "meta:tree"
_IDX_PREFIX = "meta:tree_idx"
_IDS_KEY = "meta:tree_ids"


@dataclass
class CacheTree:
    tree_id: str
    name: str
    parent_tree_id: str = ""
    status: str = "active"  # active | frozen | archived
    default: bool = False
    created_at: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "CacheTree":
        data = json.loads(raw)
        return CacheTree(
            tree_id=str(data.get("tree_id") or ""),
            name=str(data.get("name") or ""),
            parent_tree_id=str(data.get("parent_tree_id") or ""),
            status=str(data.get("status") or "active"),
            default=bool(data.get("default")),
            created_at=int(data.get("created_at") or 0),
        )


def _meta_key(tenant: str, tree_id: str) -> str:
    return f"at:{tenant}:{_META_PREFIX}:{tree_id}"


def _idx_key(tenant: str, tree_id: str) -> str:
    return f"at:{tenant}:{_IDX_PREFIX}:{tree_id}"


def _ids_key(tenant: str) -> str:
    return f"at:{tenant}:{_IDS_KEY}"


def blob_key_for(tenant: str, tree_id: str, digest: str) -> str:
    """Redis key for a digest in a tree (v2 main / v3 named)."""
    if tree_id == DEFAULT_CACHE_TREE:
        return f"at:{tenant}:cache:v2:{digest}"
    return f"at:{tenant}:tree:{tree_id}:cache:v3:{digest}"


class CacheTreeRegistry:
    def __init__(self, store: CacheStore):
        self._store = store

    async def ensure_main(self, tenant: str) -> CacheTree:
        existing = await self.get(tenant, DEFAULT_CACHE_TREE)
        if existing:
            return existing
        tree = CacheTree(
            tree_id=DEFAULT_CACHE_TREE,
            name=DEFAULT_CACHE_TREE,
            parent_tree_id="",
            status="active",
            default=True,
            created_at=int(time.time()),
        )
        await self._save(tenant, tree)
        await self._add_id(tenant, tree.tree_id)
        return tree

    async def get(self, tenant: str, tree_id: str) -> Optional[CacheTree]:
        raw = await self._store.get(_meta_key(tenant, tree_id))
        if not raw:
            return None
        return CacheTree.from_json(raw)

    async def list(self, tenant: str) -> list[CacheTree]:
        await self.ensure_main(tenant)
        raw = await self._store.get(_ids_key(tenant))
        ids = json.loads(raw) if raw else [DEFAULT_CACHE_TREE]
        out: list[CacheTree] = []
        for tid in ids:
            t = await self.get(tenant, tid)
            if t:
                out.append(t)
        return out

    async def _save(self, tenant: str, tree: CacheTree) -> None:
        await self._store.set(_meta_key(tenant, tree.tree_id), tree.to_json(), ttl_seconds=0)

    async def _add_id(self, tenant: str, tree_id: str) -> None:
        raw = await self._store.get(_ids_key(tenant))
        ids = json.loads(raw) if raw else []
        if tree_id not in ids:
            ids.append(tree_id)
            await self._store.set(_ids_key(tenant), json.dumps(ids), ttl_seconds=0)

    async def fork(
        self,
        tenant: str,
        *,
        name: str,
        parent: str | None = None,
    ) -> CacheTree:
        name_id = resolve_cache_tree(body=name)
        if name_id == DEFAULT_CACHE_TREE:
            raise ValueError("cannot_fork_main")
        parent_id = resolve_cache_tree(body=parent) if parent else DEFAULT_CACHE_TREE
        await self.ensure_main(tenant)
        if await self.get(tenant, name_id):
            raise ValueError("tree_exists")
        parent_tree = await self.get(tenant, parent_id)
        if parent_tree is None:
            raise ValueError("parent_missing")
        if parent_tree.status == "archived":
            raise ValueError("parent_archived")
        tree = CacheTree(
            tree_id=name_id,
            name=name_id,
            parent_tree_id=parent_id,
            status="active",
            default=False,
            created_at=int(time.time()),
        )
        await self._save(tenant, tree)
        await self._add_id(tenant, tree.tree_id)
        await self._store.set(_idx_key(tenant, tree.tree_id), json.dumps([]), ttl_seconds=0)
        return tree

    async def reset(
        self,
        tenant: str,
        tree_id: str,
        *,
        to: str = "empty",
    ) -> CacheTree:
        tree = await self.get(tenant, tree_id)
        if tree is None:
            raise ValueError("tree_missing")
        if tree.tree_id == DEFAULT_CACHE_TREE:
            raise ValueError("cannot_reset_main")
        if tree.status == "frozen":
            raise ValueError("tree_frozen")
        if to == "empty":
            await self._store.set(_idx_key(tenant, tree.tree_id), json.dumps([]), ttl_seconds=0)
        elif to == "parent":
            # Drop local overrides index; COW still reads parent chain.
            await self._store.set(_idx_key(tenant, tree.tree_id), json.dumps([]), ttl_seconds=0)
        else:
            raise ValueError("invalid_reset_to")
        return tree

    async def freeze(self, tenant: str, tree_id: str) -> CacheTree:
        tree = await self.get(tenant, tree_id)
        if tree is None:
            raise ValueError("tree_missing")
        if tree.tree_id == DEFAULT_CACHE_TREE:
            raise ValueError("cannot_freeze_main")
        tree.status = "frozen"
        await self._save(tenant, tree)
        return tree

    async def ensure_tree(self, tenant: str, tree_id: str) -> CacheTree:
        """Return tree meta; lazy-create named trees under ``main`` (Phase 0 select)."""
        await self.ensure_main(tenant)
        if tree_id == DEFAULT_CACHE_TREE:
            return await self.ensure_main(tenant)
        existing = await self.get(tenant, tree_id)
        if existing:
            return existing
        tree = CacheTree(
            tree_id=tree_id,
            name=tree_id,
            parent_tree_id=DEFAULT_CACHE_TREE,
            status="active",
            default=False,
            created_at=int(time.time()),
        )
        await self._save(tenant, tree)
        await self._add_id(tenant, tree.tree_id)
        await self._store.set(_idx_key(tenant, tree.tree_id), json.dumps([]), ttl_seconds=0)
        return tree

    async def assert_writable(self, tenant: str, tree_id: str) -> CacheTree:
        tree = await self.ensure_tree(tenant, tree_id)
        if tree.status == "frozen":
            raise ValueError("tree_frozen")
        if tree.status == "archived":
            raise ValueError("tree_archived")
        return tree

    async def index_add(self, tenant: str, tree_id: str, digest: str) -> None:
        key = _idx_key(tenant, tree_id)
        raw = await self._store.get(key)
        digests = json.loads(raw) if raw else []
        if digest not in digests:
            digests.append(digest)
            await self._store.set(key, json.dumps(digests), ttl_seconds=0)

    async def index_list(self, tenant: str, tree_id: str) -> list[str]:
        raw = await self._store.get(_idx_key(tenant, tree_id))
        return json.loads(raw) if raw else []

    async def parent_chain(self, tenant: str, tree_id: str) -> list[str]:
        """tree_id first, then parents up to COW_DEPTH_CAP."""
        chain: list[str] = []
        cur = tree_id
        for _ in range(COW_DEPTH_CAP):
            if not cur or cur in chain:
                break
            chain.append(cur)
            meta = await self.get(tenant, cur)
            if meta is None or not meta.parent_tree_id:
                break
            cur = meta.parent_tree_id
        return chain

    async def get_blob_cow(
        self, tenant: str, tree_id: str, digest: str
    ) -> tuple[Optional[str], str]:
        """Return (payload, served_tree_id) walking COW parents."""
        for tid in await self.parent_chain(tenant, tree_id):
            raw = await self._store.get(blob_key_for(tenant, tid, digest))
            if raw is not None:
                return raw, tid
        return None, tree_id

    async def promote(
        self,
        tenant: str,
        tree_id: str,
        *,
        into: str | None = None,
        ttl_seconds: int = 3600,
    ) -> dict[str, Any]:
        child = await self.get(tenant, tree_id)
        if child is None:
            raise ValueError("tree_missing")
        if child.tree_id == DEFAULT_CACHE_TREE:
            raise ValueError("cannot_promote_main")
        parent_id = into or child.parent_tree_id or DEFAULT_CACHE_TREE
        parent = await self.get(tenant, parent_id)
        if parent is None:
            raise ValueError("parent_missing")
        if parent.status == "frozen":
            raise ValueError("parent_frozen")
        digests = await self.index_list(tenant, child.tree_id)
        copied = 0
        for digest in digests:
            src = await self._store.get(blob_key_for(tenant, child.tree_id, digest))
            if src is None:
                # May live only via deeper COW — skip missing local writes
                continue
            dst = blob_key_for(tenant, parent_id, digest)
            await self._store.set(dst, src, ttl_seconds=ttl_seconds)
            await self.index_add(tenant, parent_id, digest)
            copied += 1
        return {
            "from": child.tree_id,
            "into": parent_id,
            "digests_considered": len(digests),
            "digests_copied": copied,
        }


def new_tree_id_hint() -> str:
    return "t-" + uuid.uuid4().hex[:10]
