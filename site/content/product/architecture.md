---
title: Architecture
description: One OpenAI-compatible gateway. Two containers. One metered crossing — and tips so inventory stays honest.
---

## Shape

withOhm is an OpenAI-compatible AI gateway. Clients send `/v1/chat/completions` (and related routes) with a Bearer key. withOhm applies seat checks, Redis exact-replay, BYOK to the model provider, and Stripe metering. The response is OpenAI-shaped.

That is the whole product surface. Everything else is how inventory is addressed — and how governance stays off the hot path.

If you have used a single opaque proxy before, the mental model shift is small but load-bearing: **replay lives in one container; money and policy live in another.** They meet at HIT or MISS. They do not blur into each other.

The methodical cut of the same design lives in [Docs — Architecture](/docs/architecture). This page is the walkthrough: tips, Promote, compose, and the anti-pattern we see when teams skip the tip.

## Gateway

One URL. One key path. Cursor, CI, and agents use the same OpenAI-compatible contract. You do not learn a new protocol to get exact-replay; you point the client you already have.

```bash
curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role":"user","content":"ping"}]
  }'
```

Exact replay is Redis-backed: same request fingerprint on the same tip returns the stored completion when present. Misses go BYOK to the provider and are written back. Ambient fact: the fingerprint is exact. Soft or semantic “close enough” matching is not part of the pipe — receipts would stop meaning anything if it were.

## Two containers

On every request the edge and the control plane cooperate as two containers:

- **Ephemeral Side** — edge HIT, cache trees, content-addressed blobs, BYOK request context. Optimized for latency and mechanical repeat. Safe to TTL or freeze without erasing your ledger.
- **Pipeline System** — tenancy, Stripe meters, compliance ingest, provider route, JWKS receipts, org audit / FinOps. Optimized for claims you can stand behind.

They meet at a metered **HIT / MISS** crossing. HIT never calls the lab. MISS does — then stores, unless you said `no_store`.

Streaming rides the same split with an honest limit: pre-first-byte failover is shipped; mid-stream handoff is not. Details: [Streaming & failover](/docs/streaming).

## Tips

A **tip** is a named address in the exact-replay inventory. Clients select it with `X-Ohm-Cache-Tree`.

Default tip is `main` — durable inventory for the shared path. Ephemeral tips (`pr-842`, `agent-a`, suite names) keep work off `main` until Promote. Dashed frames in the diagrams are ephemeral. Hatch is durable `main`.

```bash
curl -sS https://api.withohm.dev/v1/chat/completions \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Ohm-Cache-Tree: pr-842" \
  -d @prompt.json
```

<!-- ohm:cache-trees -->

Collisions happen when two writers share one tip — not because the gateway is shared. That distinction is the whole tip story in one sentence. Keep one gateway. Split tips when streams should not pollute each other.

## Crossing

**Promote** is the only intentional write from an ephemeral tip onto `main`. Until Promote, `main` does not absorb that tip’s inventory. After Promote, the next job on `main` can HIT those entries.

<!-- ohm:crossing -->

Billing stays on the shared gateway (seats + meters). Promote is inventory hygiene, not a second SKU. Purple in the diagrams is that crossing — the moment preview work earns durable inventory.

## Compose

Optional database preview branches carry **database state**. Ohm tips carry **exact-replay inventory**. CI can compose both: a preview `DATABASE_URL` (or equivalent) plus `X-Ohm-Cache-Tree`. Same job. Two headers. Clear nouns. Dedicated guide: [Compose with Neon](/docs/compose-neon).

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
curl -sS -X POST "https://api.withohm.dev/v1/cache/trees/${OHM_TIP}/promote" \
  -H "Authorization: Bearer $OHM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target":"main"}'
```

withOhm does not replace the database preview. It is the inventory peer in the same workflow. If you already branch state for PRs, pairing a tip is the smallest change that stops preview prompts from warming production HITs by accident.

## Anti-pattern

Putting every agent on `main`, then spinning a second gateway when collisions appear, buys keys — not isolation.

<!-- ohm:noisy-neighbor -->

Isolation is a tip problem. Keep one gateway. Split tips. Promote when the suite earns `main`. The noisy-neighbor diagram is not a morality play; it is the failure mode we see when the gateway is shared for the right reason and the tip is shared for the wrong one.

## What this architecture enables

<!-- ohm:enablement -->

## Related

- [Docs — Architecture](/docs/architecture) — methodical dual-container deep dive
- [Inventory per tenant](/use-cases/inventory-per-tenant) — tip isolation walkthrough
- [Docs — Cache trees](/docs/cache-trees)
- [Docs — Compose with Neon](/docs/compose-neon)
- [Docs — Edge](/docs/edge)
- [Docs — Streaming](/docs/streaming)
- [Pricing](/pricing)
