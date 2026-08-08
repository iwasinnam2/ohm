# Security

withOhm sits between your apps and upstream model providers.

## What is cached

Identical chat completion requests (per tenant) may store the model response in Redis for the configured TTL. Cache keys are derived from tenant + model + messages (+ web-fetch extras). Purpose header: `X-AT-Cache-Purpose: identical-request-replay`.

## Retention

- Default TTL is operator-configurable (3600s locally)
- Ledger counters persist for metering; aggregates, not full prompts
- Opt-out: `cache_control: "no_store"` or enterprise no-store arrangements

## Keys

- Customer keys stored hashed (SHA-256) at rest
- Issued prefix today: `sk-at-…` (withOhm brand; rename deferred)
- Suspended tenants → HTTP 403

## Subprocessors

Model providers you enable, Amazon Web Services (or host), Stripe (billing), AWS Amplify (docs/marketing site).

## Headers (legacy `AT` family)

| Header | Meaning |
|--------|---------|
| `X-AT-Cache` | `HIT` / `MISS` / `BYPASS` |
| `X-AT-Cache-Purpose` | `identical-request-replay` |
| `X-AT-Region` | Serving region |
| `x-at-plane` | `rust` when via Rust edge |
| `X-Ohm-Path` | Frequency-farm path label (normalized); echoed when set |
| `X-Ohm-Cost-Center` | Cost-center attribution |
| `X-Ohm-Spend-Cap` / `X-Ohm-Spend-Cap-Usd` | Soft spend-cap notice on allowed MISS |

Clean ledger events include `path` (default `default`). Public receipt threat model unchanged — unguessable token, no prompts.
