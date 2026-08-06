# Architecture

Public cut of the dual-container design. Narrative deep dive: [Product — Architecture](/product/architecture).

## Two containers

1. **Ephemeral Side** — edge HIT, cache trees, content-addressed blobs, BYOK request context.
2. **Pipeline System** — tenancy, Stripe meters, compliance ingest, provider route, JWKS receipts, org audit / FinOps.

They meet at a metered **HIT / MISS** crossing.

## Fence

Neon branches **database state**. withOhm branches **exact-replay inventory**. Compose with `NEON_BRANCH` + `X-Ohm-Cache-Tree`. Do not treat cache trees as Postgres branches.

## Hierarchy

| Concept | Role |
|---------|------|
| Organization | SSO, policy, FinOps |
| Tenant | Billing / meter identity |
| Cache tree | Named exact-replay inventory |
| API key | Auth material bound to a tenant |
| Path / cost center | Ledger dimensions — not cache partitions |

## See also

- [Cache trees](/docs/cache-trees)
- [Edge](/docs/edge)
- [Compose with Neon](/docs/compose-neon)
- [Honesty](/docs/honesty)
- [Receipts](/docs/receipts)
