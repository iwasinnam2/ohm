# Compose with Neon

**withOhm — middleware governance.** Exact-replay inventory that pairs with Neon’s branch model — including Neon AI Gateway beta — without competing for the database noun.

Neon owns **database state** (and, in beta, a branch-scoped AI Gateway). withOhm owns **exact-replay inventory**. Same CI job. Same PR slug. Clear peers.

<!-- ohm:compose-ci -->

## Fence

| Product | Branches | Noun |
| --- | --- | --- |
| Neon | Database state (+ AI Gateway endpoint per branch in beta) | Preview connection / branch |
| withOhm | Exact-replay inventory | `X-Ohm-Cache-Tree` |

Neon does **not** replace Ohm. Ohm does **not** replace Neon. A preview database will not isolate mechanical prompt HITs. A cache tip will not version your schema. Neon AI Gateway routes models on the branch; withOhm meters exact-replay crossings on the tip.

Ambient note: if you already create a Neon branch per PR, adding `X-Ohm-Cache-Tree: pr-$NUMBER` is usually the smallest change that stops preview prompts from warming production inventory.

## One-slug discipline

Use the same slug for both peers:

```text
pr-${PR_NUMBER}
```

- Neon preview branch: `pr-842`
- Ohm tip: `pr-842`
- On merge: handle Neon branch lifecycle as you already do; **Promote** the Ohm tip into `main`

## Drop-in CI starter

Clone-ready workflows + scripts:

**[templates/neon-ohm-ci](https://github.com/iwasinnam2/ohm/tree/master/templates/neon-ohm-ci)**

| Workflow | When | What |
| --- | --- | --- |
| `ohm-preview.yml` | Every PR | Ensure tip `pr-N`; smoke chat with the tip header |
| `ohm-promote-on-merge.yml` | PR merged | `POST /v1/cache/trees/pr-N/promote` |

Secrets: `OHM_API_KEY`. Optional var: `OHM_API_URL` (default `https://api.withohm.dev`).

## Typical CI recipe

1. Create or select a Neon branch for app schema and data under test (and AI Gateway on that branch if you use the beta).
2. Fork or select an Ohm tip named after the PR (`pr-842`).
3. Point the app at the Neon connection string; point agents and tests at `api.withohm.dev/v1` with `X-Ohm-Cache-Tree: pr-842`.
4. On merge: Promote the Ohm tip; handle Neon branch lifecycle separately.

```bash
export DATABASE_URL="$NEON_PREVIEW_URL"
export OHM_TIP="pr-${PR_NUMBER}"
export OHM_API_URL=https://api.withohm.dev

curl -sS -X POST "$OHM_API_URL/v1/cache/trees" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$OHM_TIP\"}"

curl -sS "$OHM_API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: $OHM_TIP" \
  -d @prompt.json
```

On green, Promote is inventory hygiene — not a second bill:

```bash
curl -sS -X POST "$OHM_API_URL/v1/cache/trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Why this is an upgrade alongside AI Gateway beta

Neon AI Gateway already gives one credential and a branch-scoped model path. withOhm adds middleware governance on repeats: exact-match Redis inventory, tip isolation, Promote-on-merge, HIT meters, and receipts. Labs stay labs. Neon stays the backend center. Ohm rents the pipe on mechanical repetition.

## Related

- [Architecture](/docs/architecture)
- [Cache trees](/docs/cache-trees)
- [CI preview](/use-cases/ci-preview)
- [Inventory per tenant](/use-cases/inventory-per-tenant)
- [Streaming & failover](/docs/streaming)
