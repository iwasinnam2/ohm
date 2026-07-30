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

**Core slogan (four pillars):**

> Exact-replay hits that cost zero upstream tokens. Cross-provider consistency. Locality — Redis edge reads. Replay and audit value.

1. **Zero-token replay** — identical requests answer from Redis; the provider is never paid twice. Provider-native prompt caching discounts prefix *reuse*; only an external exact-replay cache makes the second identical call cost **zero** upstream tokens.
2. **Cross-provider consistency** — one OpenAI-shaped pipe and one cache contract across OpenAI, Anthropic, Gemini, DeepSeek, Moonshot/Kimi, Z.ai/GLM, Qwen, and xAI/Grok (BYOK).
3. **Locality / latency** — cache GETs on the nearest Redis edge replica; pre-first-byte failover keeps the pipe honest.
4. **Replay / audit value** — every hit is an auditable identical-request replay with a readable meter; never a training corpus.

> Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.

## Non-goal

Ohm as a PAYG wholesale reseller of OpenAI/Anthropic tokens for self-serve plans.
