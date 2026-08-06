Give every PR, agent, or customer stream a dedicated exact-replay namespace. Meet isolation needs, eliminate cross-suite cache pollution, and scale mechanical AI traffic without sharing one hot `main` tip.

## Summary

withOhm makes it straightforward to isolate each workload in its own **cache tree** — instance-level isolation for **exact-replay inventory**, without the cost of spinning a new model gateway or Postgres per tenant.

- **No more noisy neighbors** — Suites and agents write HITs into named trees; one runaway job does not poison everyone else’s replay path.
- **Simplified compliance story** — Replay stays inventory, never a training corpus; trees do not widen purpose or retention.
- **Scale each stream independently** — Fork, promote, freeze, and TTL trees without resizing a shared opaque cache.
- **Promote without copying blobs** — Content-addressed digests; promote merges tips, not byte-for-byte clones.
- **API-first management** — List, fork, reset, promote, freeze over `/v1/cache/trees`.

Start with a [$0 Intermediate seat](/billing/intermediate), then follow [Cache trees](/docs/cache-trees).

## Why inventory-per-tenant?

When you put agents and CI on an OpenAI-compatible pipe, multitenancy shows up as **who shares which HITs**:

- **Privacy & blast radius** — Regulated teams may require that one customer’s or one PR’s replay inventory never bleeds into another.
- **Clean promote paths** — Preview trees promote into `main` the way preview DBs promote schema — for digests, not rows.
- **Independent freeze / reset** — Freeze a tip for audit; reset a failed suite without wiping the org.
- **Avoid noisy neighbors** — Shared caches turn one flaky suite into everyone else’s mystery HITs.

<!-- ohm:cache-trees-flowchart -->

## Sharing one global cache for everything is not a good idea

Gateway caches that dump all tenants into one keyspace look cheap until they are not.

### 1. Cramming every suite into `main`

- **Single polluted tip** — Bad digests or oversized prompts land where production agents also read.
- **Noisy neighbors** — A CI stampede evicts or confuses inventory others still need.
- **Awkward ops** — You cannot freeze “just the PR” or reset “just the agent”.
- **Rigid scaling** — You scale the whole shared cache story even when only one stream is hot.

### 2. Standing up a whole new gateway per tenant

Isolation by deploying N copies of the pipe:

- **Expensive and slow** — Provisioning lag kills PR preview UX.
- **No shared blob economics** — You lose content-addressed dedupe across trees.
- **Ops burden** — Keys, meters, and honesty multiply with each snowflake stack.

> We needed PR-scoped replay without teaching every engineer a second database product — cache trees are the git-shaped surface for exact-replay, not a Neon clone.

## Exact-replay the way multi-tenant agent CI was meant to work

withOhm keeps one pipe and partitions inventory with **cache trees**. Each tree is a named namespace over digests. Default `main` keeps today’s keys; named trees use the v3 layout. Neon still owns database branches. Ohm owns replay branches.

### One tree per stream

- Completely separate HIT namespaces per tree id
- Independent promote / freeze / reset
- Optional tree claims on receipts and audit events
- No resource contention on the digest tip between suites

### Scale each stream independently

Busy PR trees accumulate HITs; idle ones cost nothing beyond Redis TTL policy. You do not provision a new RDS-shaped cache appliance per customer.

### Promote a single stream without touching the fleet

Promote merges child digests into the parent. Other trees keep serving. Frozen tips reject writes (409) while HITs continue.

### API-first management

```bash
curl -s https://api.withohm.dev/v1/cache/trees \
  -H "Authorization: Bearer $OHM_API_KEY"

curl -s -X POST https://api.withohm.dev/v1/cache/trees \
  -H "Authorization: Bearer $OHM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"pr-842"}'
```

Send `X-Ohm-Cache-Tree: pr-842` on chat completions. Details: [API docs](/docs/api) · [Cache trees](/docs/cache-trees).

### Compliance and trust

- Exact-replay purpose unchanged — trees do not create a training corpus
- Honesty map stays public: [Honesty](/docs/honesty)
- Signed HIT receipts may carry `tree_id` / `tree_name`: [Receipts](/docs/receipts)
- Security posture: [Security](/docs/security)

### Compose with Neon for data + Ohm for replay

Keep a Neon branch for application state. Keep an Ohm cache tree for exact-replay inventory. Same CI job; different nouns. Guide: [Compose with Neon](/docs/compose-neon).

### Start building

[Start now — $0 seat](/billing/intermediate) · [CI preview solution](/use-cases/ci-preview) · [Product: Cache trees](/product/cache-trees)
