# Compose with Neon

Neon and withOhm solve different branching problems. Use both in one CI job.

## Fence

| Product | Branches | Noun |
|---------|----------|------|
| Neon | Database state | `NEON_BRANCH` / project branch |
| withOhm | Exact-replay inventory | `X-Ohm-Cache-Tree` |

Neon does **not** replace Ohm. Ohm does **not** replace Neon.

## Typical CI recipe

1. Create or select a Neon branch for app schema/data under test.
2. Fork or select an Ohm cache tree named after the PR (`pr-842`).
3. Point the app at the Neon connection string; point agents/tests at `api.withohm.dev/v1` with `X-Ohm-Cache-Tree: pr-842`.
4. On merge: promote or freeze the Ohm tree per policy; handle Neon branch lifecycle separately.

## Why

Preview databases keep state honest. Preview inventory keeps mechanical prompts from polluting `main` HITs. Solutions: [CI preview](/use-cases/ci-preview) · [Inventory per tenant](/use-cases/inventory-per-tenant).
