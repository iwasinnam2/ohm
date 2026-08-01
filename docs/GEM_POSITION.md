# Gem position — withOhm

Canonical wedge for product, GTM, and Cursor Marketplace / BD.

## The inefficiency

Agent products (Cursor included) scale context across consecutive turns: tool
results, retrieved files, compacted history. Naive routing **re-pays prefill**
on every call. Compaction / “context summarised” is a pressure valve — it does
not remove the economic waste of identical or near-mechanical repeats
(retries, loops, CI prompt suites, stable system+file pairs).

## The gem

withOhm is the **tollbooth on wasted and repeated inference**:

| Layer | Role |
|-------|------|
| Labs (OpenAI / Anthropic / xAI) | Generation + model billing (BYOK) |
| Cursor / agent hosts | Cockpit + context assembly |
| **withOhm** | Metered pipe: exact-match Redis replay + compliant web ingest |

We do **not** sell bigger context windows, wholesale tokens, or an IDE.
We rent plumbing that makes context scaling *economically* survivable.

## Promise

> Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain
> prompt replay, a clearer pipe, compliant web context — and a bill that rents
> the plumbing, not the model.

## Dual savings ledger (proof contract)

`GET /v1/savings` / receipts / `ohm_savings`:

| Field | Meaning |
|-------|---------|
| `estimated_provider_avoided_usd` | Hit tokens × blended provider list rate (`AT_PROVIDER_AVOIDED_PER_1K_TOKENS`, default $15/M) |
| `pipe_rent_usd` | What Ohm metered (hits + misses + fetches) |
| `roi_ratio` | Provider avoided ÷ pipe rent (“$X saved per $1 of pipe”) |
| `estimate_only` | Always true — not a guarantee |

`estimated_upstream_avoided_usd` aliases the provider figure for backward
compatibility. Badges and public receipts use that hero number.

## Non-goals

- Semantic / fuzzy cache (near-miss → refunds)
- PAYG reseller of OpenAI/Anthropic tokens on self-serve
- Replacing Cursor model billing or Composer UX
- Guaranteed savings SLAs

## Cursor attention (two layers)

1. **Users** — Marketplace, Forum, receipts: agents burn less upstream $.
2. **Company** — [CURSOR_BD_BRIEF.md](distribution/CURSOR_BD_BRIEF.md) + refreshed
   Marketplace listing for employee review: platform economics without Cursor
   owning cache middleware or compliance browse.

Vision ledger: [VISION.md](VISION.md). Pricing honesty: [PRICING.md](PRICING.md).
