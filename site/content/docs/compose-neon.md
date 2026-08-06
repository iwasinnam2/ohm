# Compose with Neon

Neon and withOhm solve different branching problems. Use both in one CI job when the PR needs honest state *and* honest replay inventory.

This is not a rivalry page. It is a compose guide: keep the nouns straight, wire both peers, promote when the suite earns `main`.

## Fence

| Product | Branches | Noun |
| --- | --- | --- |
| Neon (or peer) | Database state | Preview connection / `NEON_BRANCH` |
| withOhm | Exact-replay inventory | `X-Ohm-Cache-Tree` |

Neon does **not** replace Ohm. Ohm does **not** replace Neon. A preview database will not isolate mechanical prompt HITs. A cache tip will not version your schema. Teams get into trouble when they ask one peer to do the other’s job.

Ambient note: if you already create a database branch per PR, adding `X-Ohm-Cache-Tree: pr-$NUMBER` is usually the smallest change that stops preview prompts from warming production inventory.

## Typical CI recipe

1. Create or select a Neon branch for app schema and data under test.
2. Fork or select an Ohm cache tip named after the PR (`pr-842`).
3. Point the app at the Neon connection string; point agents and tests at `api.withohm.dev/v1` with `X-Ohm-Cache-Tree: pr-842`.
4. On merge: promote or freeze the Ohm tip per policy; handle Neon branch lifecycle separately.

```bash
export DATABASE_URL="$NEON_PREVIEW_URL"
export OHM_TIP="pr-${PR_NUMBER}"

curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: $OHM_TIP" \
  -d @prompt.json
```

On green, Promote is inventory hygiene — not a second bill:

```bash
curl -sS -X POST "https://api.withohm.dev/v1/cache-trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target":"main"}'
```

## Why

Preview databases keep state honest. Preview inventory keeps mechanical prompts from polluting `main` HITs. Together they make the PR suite look like production without forcing production to absorb every experimental completion.

Architecture context: [Architecture](/docs/architecture). Solutions: [CI preview](/use-cases/ci-preview) · [Inventory per tenant](/use-cases/inventory-per-tenant).
