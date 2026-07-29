# Security

Ohm sits between your apps and upstream model providers.

## What is cached

Identical chat completion requests (per tenant) may store the model response in Redis for the configured TTL. Cache keys are derived from tenant + model + messages (+ web-fetch extras). Purpose header: `X-AT-Cache-Purpose: identical-request-replay`.

## Retention

- Default TTL via `AT_CACHE_TTL_SECONDS` (3600 locally)
- Ledger counters persist for metering; aggregates, not full prompts
- Opt-out: `cache_control: "no_store"` or enterprise no-store arrangements

## Keys

- Customer keys stored hashed (SHA-256) at rest
- Issued prefix today: `sk-at-…` (Ohm brand; rename deferred)
- Suspended tenants → HTTP 403

## Subprocessors

Model providers you enable, Amazon Web Services (or host), Stripe (billing), Vercel (docs site).

## Headers (legacy `AT` family)

| Header | Meaning |
|--------|---------|
| `X-AT-Cache` | `HIT` / `MISS` / `BYPASS` |
| `X-AT-Cache-Purpose` | `identical-request-replay` |
| `X-AT-Region` | Serving region |
| `x-at-plane` | `rust` when via Rust edge |
