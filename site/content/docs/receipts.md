# Waste demo

Live proof that mechanical repeats stop re-buying the model.

Open the interactive demo: **[Waste demo](/product/waste-demo)**.

## What you see

1. First identical call → **MISS** — Pipeline routes BYOK (or mock); pipe rent `ohm_cache_miss`.
2. Second identical call → **HIT** — Ephemeral Redis replay; labs silent; pipe rent `ohm_cache_hit`.
3. Dual ledger — estimated provider spend avoided vs Ohm pipe rent (`/v1/savings`).

## Why it matters

Agent retries, research loops, and CI suites re-pay prefill when every call goes bare to a lab. withOhm intercepts the crossing: inventory stays in Ohm; labs are called only on MISS.

## Next

- [Create Account](/signup) — Intermediate email + password
- [Attach in Cursor](/i)
- [Architecture](/docs/architecture)
