# Cache trees — ADR (Phase 0)

Branchable **exact-replay** inventory for withOhm. Complements Neon (data branches);
does not clone Postgres branching.

Parent architecture (Neon-grammar overview): [ARCHITECTURE.md](ARCHITECTURE.md).

## Dual containers

| Ephemeral Side | Pipeline System |
|----------------|-----------------|
| Hot exact-replay inventory (blobs, trees, edge HIT) | Durable money, policy, compliance, trust |
| Fork / reset / promote / freeze (Phase 1+) | Auth, meters, receipts, audit |

**Slogan to earn:** Neon branches state. Labs discount prefixes. Ohm branches exact replay — and the pipeline bills the crossing.

## Key layout

| Tree | Redis key |
|------|-----------|
| Default `main` (no header) | `at:{tenant}:cache:v2:{digest}` — **unchanged** HIT behavior |
| Named tree | `at:{tenant}:tree:{tree_id}:cache:v3:{digest}` |

- `digest` is always the **last** `:` segment (receipts `request_sha256`).
- `tree_id`: `[a-z0-9_-]{1,64}`; header `X-Ohm-Cache-Tree` wins over body `cache_tree`.
- Unknown / invalid explicit tree → **400**.
- Exact-match only inside a tree. No semantic cache. No cross-tenant trees.

### Storage honesty (CAS vs COW)

Named-tree blobs use **per-tree Redis keys**. COW **reads** walk the parent
chain and may serve a parent blob without copying it into the child. That is
**not** yet a single shared content-addressed object store with many refs
(Phase 3). Promote still **copies** child-local digests into the parent key
space. Do not claim “zero duplication” or “one blob, many refs” until Phase 3
refcount CAS ships.

## Client surface (Phase 0)

- Header: `X-Ohm-Cache-Tree: pr-842` (optional)
- Body: `cache_tree` (optional; header wins)
- Response echo: `X-Ohm-Cache-Tree`

## Non-goals

- Postgres / WAL / schema branch / Neon API cosplay
- Semantic / fuzzy cache
- Cross-tenant shared trees
- Visual redesign of the marketing site (separate track)

## Phases

| Phase | Scope |
|-------|--------|
| **0** | Spec, resolve, v3 keys for named trees, dual-plane parity, honesty/LEGAL/SECURITY stubs |
| **1–2 (this)** | Fork / reset / promote / freeze APIs, COW reads, digest index, receipt `tree_*`, audit actions |
| 3 | Shared blob store efficiency (refcount GC / true single-CAS) — **not shipped**; see Storage honesty above |
| 4 | Retain / restore (legal Duration first) |
| 5 | Org ACLs / quotas |

### API (Phases 1–2)

| Method | Path | Role |
|--------|------|------|
| `GET` | `/v1/cache/trees` | List trees |
| `POST` | `/v1/cache/trees` | Fork `{name, parent?}` |
| `POST` | `/v1/cache/trees/{id}/reset` | `{to: empty\|parent}` |
| `POST` | `/v1/cache/trees/{id}/promote` | Merge child digests into parent |
| `POST` | `/v1/cache/trees/{id}/freeze` | Immutable tip; writes → 409 |

Audit: `cache.tree_fork`, `cache.tree_reset`, `cache.tree_promote`, `cache.tree_freeze`, deny variants.

## Neon fence

Compose in CI: `NEON_BRANCH` + `X-Ohm-Cache-Tree` with the same PR slug. Do not claim database branching.
