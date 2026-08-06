Give every pull request its own exact-replay tree. Run the suite. Promote digests into `main` when green. Compose with Neon branches for database state.

## Summary

- **Fork per PR** — `X-Ohm-Cache-Tree: pr-842`
- **HIT isolation** — Preview does not pollute production agent inventory
- **Promote** — Merge child tips into parent without copying blobs
- **Freeze** — Lock a tip for audit after release
- **Compose** — `NEON_BRANCH` + Ohm tree in the same workflow

<!-- ohm:cache-trees-flowchart -->

## Why CI needs replay trees

Prompt suites are mechanical. Without trees, every PR writes into one shared tip — or you disable caching and burn tokens. Trees are the git-shaped surface for **inventory**, not schema.

## Anti-pattern: staging gateway + hope

A second full stack per PR is slow and expensive. A shared cache is fast and unsafe. Cache trees are the middle path.

## How we win

1. CI forks a tree (or uses a deterministic name).
2. Jobs send the tree header on chat completions.
3. On merge: promote (or freeze, then promote policy of your choice).
4. Neon handles DB preview; Ohm handles replay preview.

Guide: [Compose with Neon](/docs/compose-neon) · Docs: [Cache trees](/docs/cache-trees)

## Start

[Inventory per tenant](/use-cases/inventory-per-tenant) · [Product: Cache trees](/product/cache-trees) · [$0 seat](/billing/intermediate)
