---
title: Inventory per tenant
description: Same model. Same gateway. Separate tips — so agent runs do not collide on main.
---

<!-- ohm:noisy-neighbor -->

## The problem

Teams often put every agent, CI job, and PR on one tip — usually `main`. The gateway is shared for the right reason (one BYOK path, one bill). The tip is shared for the wrong reason.

When two agents land different prompts on the same tip, the second write collides. Retries look like flaky LLM output. Engineers add a second gateway “for tenant B,” and now you have two keys, two meters, and still no tip discipline.

That is the noisy-neighbor pattern. Isolation is a tip problem, not a second-gateway problem.

## What withOhm does

withOhm keeps one OpenAI-compatible gateway and one Stripe bill. Isolation is a **cache tip** — a named tip in the Redis exact-replay inventory, addressed as `X-Ohm-Cache-Tree`.

| Shared (good) | Separated (also good) |
| --- | --- |
| Gateway URL | Cache tip per agent / PR / suite |
| BYOK path to the model | Exact-replay inventory on that tip |
| Seat + meter on Stripe | Promote when the suite earns main |

Same model. Same gateway. Separate tips.

<!-- ohm:crossing -->

## Promote is the only crossing

Work stays on the PR tip until the suite is green. Then **Promote** copies that tip onto durable `main`. Purple in the diagram is that crossing — not a second product.

Until Promote, `main` does not absorb the agent’s inventory. After Promote, the next job on `main` can hit exact replay for those entries.

## Compose with a database preview (optional)

If the PR also needs a database preview, compose it in CI. Neon (or any preview DB) is a peer for **database state**. withOhm is the peer for **exact-replay inventory**. Same job. Two headers. One bill for the model path.

```bash
# Example compose — DB preview env + Ohm tip on the same suite
export DATABASE_URL="$NEON_PREVIEW_URL"   # from your DB branch provider
export OHM_TIP="pr-${PR_NUMBER}"

curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: $OHM_TIP" \
  -d @prompt.json
```

<!-- ohm:compose-ci -->

On green:

```bash
# Promote the tip onto main (API shape — see docs for auth)
curl -sS -X POST "https://api.withohm.dev/v1/cache-trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target":"main"}'
```

## Who this is for

- Multi-agent or multi-suite CI that shares one model path
- Teams that already use preview databases and want matching inventory hygiene
- Anyone who hit collisions on `main` and almost bought a second gateway

## Related

- [Product — Architecture](/product/architecture) — tips, Promote, compose
- [Docs — Compose with Neon](/docs/compose-neon) — peer headers in CI
- [Docs — Cache trees](/docs/cache-trees) — tip semantics
- [Pricing](/pricing) — seats and meters on the shared gateway
