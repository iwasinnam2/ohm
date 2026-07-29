# Ohm vision (railgun thesis)

Ohm is an **AI traffic utility / model ingress** — invisible plumbing between builders (and Cursor/agent runtimes) and upstream models plus the public web.

## Dual gravity

1. **Latency gravity** — Localised identical-request prompt cache and a cleaner pipe so builders stop sitting on clogged dynamic-model waits (rate limits, streaming delay, duplicate middleware).
2. **Browse rocket** — Secure, purpose-bound, legally compliant public-web context (`fetch_web_context` / URL→markdown/JSON ingest). If agents stop hand-browsing, this becomes the majority of Ohm traffic and **primary variable revenue**.

## Ledger

| Path | Who pays whom | Why |
|------|---------------|-----|
| Model tokens | Customer → OpenAI/Anthropic (**BYOK**) | Adoption gravity; Cursor-honest; no wholesale float |
| Ohm pipe | Customer → Ohm (seat + meters) | Rent on cache hits/misses and the pipe gate |
| Web ingest | Customer → Ohm (fetch meter) | Ohm owns compliance land and ingest COGS |
| Enterprise managed pool | Customer → Ohm; Ohm → providers | Reserved capacity when they refuse to wait |

**BYOK-first** on the model path. Env provider keys are **dev fallback + enterprise managed pool** only. Ingest always uses Ohm-owned network.

## Distribution endgame

Ohm as a **Cursor / MCP / agent-runtime attach** — one config block, not a chat product. Cursor keeps model billing; Ohm rents cache + compliant browse.

## Promise

> Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.

## Non-goal

Ohm as a PAYG wholesale reseller of OpenAI/Anthropic tokens for self-serve plans.
