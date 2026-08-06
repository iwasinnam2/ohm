---
title: Architecture
description: One OpenAI-compatible gateway. Cache tips for inventory. Promote as the only crossing to main.
---

## Shape

withOhm is an OpenAI-compatible AI gateway. Clients send `/v1/chat/completions` (and related routes) with a Bearer key. withOhm applies seat checks, Redis exact-replay, BYOK to the model provider, and Stripe metering. The response is OpenAI-shaped.

That is the whole product surface. Everything else is how inventory is addressed.

## Gateway

One URL. One key path. Cursor, CI, and agents use the same OpenAI-compatible contract.

```bash
curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role":"user","content":"ping"}]
  }'
```

Exact replay is Redis-backed: same request fingerprint on the same tip returns the stored completion when present. Misses go BYOK to the provider and are written back.

## Tips

A **tip** is a named address in the exact-replay inventory. Clients select it with `X-Ohm-Cache-Tree`.

Default tip is `main` — durable inventory for the shared path. Ephemeral tips (`pr-842`, `agent-a`, suite names) keep work off `main` until Promote.

```bash
curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: pr-842" \
  -d @prompt.json
```

<!-- ohm:cache-trees -->

Dashed frames in the diagrams are ephemeral tips. Hatch is durable `main`. Collisions happen when two writers share one tip — not because the gateway is shared.

## Crossing

**Promote** is the only intentional write from an ephemeral tip onto `main`. Until Promote, `main` does not absorb that tip’s inventory.

<!-- ohm:crossing -->

Billing stays on the shared gateway (seats + meters). Promote is inventory hygiene, not a second SKU.

## Compose

Database preview branches (Neon and peers) carry **database state**. Ohm tips carry **exact-replay inventory**. CI composes both: `DATABASE_URL` (or equivalent) plus `X-Ohm-Cache-Tree`.

<!-- ohm:compose-ci -->

```bash
export DATABASE_URL="$NEON_PREVIEW_URL"
export OHM_TIP="pr-${PR_NUMBER}"

# suite runs against both peers…
curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: $OHM_TIP" \
  -d @prompt.json

# on green — Promote inventory to main
curl -sS -X POST "https://api.withohm.dev/v1/cache-trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target":"main"}'
```

withOhm does not replace the database preview. It is the inventory peer in the same job.

## Anti-pattern

Putting every agent on `main`, then spinning a second gateway when collisions appear, buys keys — not isolation.

<!-- ohm:noisy-neighbor -->

Isolation is a tip problem. Keep one gateway. Split tips. Promote when the suite earns `main`.

## Related

- [Inventory per tenant](/use-cases/inventory-per-tenant) — tip isolation walkthrough
- [Docs — Cache trees](/docs/cache-trees)
- [Docs — Compose with Neon](/docs/compose-neon)
- [Docs — Edge](/docs/edge)
- [Pricing](/pricing)
