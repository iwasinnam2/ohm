## Branch exact-replay inventory — not database state

Neon branches **Postgres state**. withOhm branches **exact-replay inventory**. Compose both in CI (`NEON_BRANCH` + `X-Ohm-Cache-Tree`); do not confuse the products.

Cache trees give each PR, agent, or suite its own HIT namespace: fork, promote, freeze, reset — without copying blobs and without turning replay into a training corpus.

<!-- ohm:cache-trees-flowchart -->

### Verbs that ship

| Verb | Effect |
|------|--------|
| **Fork** | Named tree from `main` (or a parent) |
| **Promote** | Merge child digests into the parent |
| **Freeze** | Tip immutable — writes return 409; HITs still serve |
| **Reset** | Empty tip or reset to parent |

Header: `X-Ohm-Cache-Tree` (or body `cache_tree`). Invalid ids → 400.

### Why trees exist

Mechanical CI and agents stampede the same prompts. Shared `main` is fine until one suite pollutes another. Trees isolate inventory the way git isolates branches — for **replay digests**, not rows.

### Docs & API

- [Cache trees docs](/docs/cache-trees)
- [Compose with Neon](/docs/compose-neon)
- [CI preview solution](/use-cases/ci-preview)
- [Inventory per tenant](/use-cases/inventory-per-tenant)
