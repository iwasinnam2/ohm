# Cache trees — ADR (Phase 0)

Branchable **exact-replay** inventory for withOhm. Complements Neon (data branches);
does not clone Postgres branching.

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
| **0 (this)** | Spec, resolve, v3 keys for named trees, dual-plane parity, honesty/LEGAL/SECURITY stubs |
| 1 | Fork / reset APIs, COW reads, CI compose, MCP |
| 2 | Promote / freeze, receipt `tree_*`, audit |
| 3 | Shared blob + index |
| 4 | Retain / restore (legal Duration first) |
| 5 | Org ACLs / quotas |

## Neon fence

Compose in CI: `NEON_BRANCH` + `X-Ohm-Cache-Tree` with the same PR slug. Do not claim database branching.
