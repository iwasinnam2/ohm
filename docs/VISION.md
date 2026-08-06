# Ohm vision — enterprise chaos governor

Ohm (withOhm) is an **AI traffic control plane** — the entropy organizer between
enterprises (and builders) and upstream models plus the public web.

Cursor is an **optional client**. We do not depend on any single IDE for
distribution or legitimacy. See [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

## Triple gravity

1. **Latency / waste gravity** — Exact-match prompt replay so mechanical agent
   loops stop re-paying full prefill.
2. **Browse / compliance gravity** — Purpose-bound, robots-aware public-web
   ingest as governed context (primary variable revenue on Intermediate).
3. **Governance gravity** — SSO tenancy, org policy, audit log, and a
   **corporate clean ledger** (cost centers, path inventory, spend caps, FinOps
   export) so abstracted enterprise AI spend becomes attributable.

## Ledger (money paths)

| Path | Who pays whom | Why |
|------|---------------|-----|
| Model tokens | Customer → labs (**BYOK**) or Ohm managed pool | Adoption vs reserved capacity |
| Ohm pipe | Customer → Ohm (seat + meters) | Rent on hits/misses and the gate |
| Web ingest | Customer → Ohm (fetch meter) | Compliance land + ingest COGS |
| Enterprise | Customer → Ohm (SKU + invoice) | SSO org, audit, managed pool, SLA path |

**BYOK-first** on Intermediate. Env provider keys = dev fallback + enterprise
managed pool only. Ingest always uses Ohm-owned network.

## Distribution endgame

1. **Primary:** OpenAI-compatible ingress + org console + **Ohm Agent Shell**
2. **Proof wedge:** Indie / design-partner meter hits (personal COGS pain)
3. **Compatibility:** MCP attach for Cursor, VS Code, Claude, custom agents

Architecture (Ephemeral Side / Pipeline System): [ARCHITECTURE.md](ARCHITECTURE.md).  
Gem (prefill waste): [GEM_POSITION.md](GEM_POSITION.md).  
Enterprise thesis: [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

## Promise

**Core slogan (four pillars):**

> Exact-replay hits that cost zero upstream tokens. Cross-provider consistency. Locality — Redis edge reads. Replay and audit value.

1. **Zero-token replay** — identical requests answer from Redis; the provider is never paid twice. Provider-native prompt caching discounts prefix *reuse*; only an external exact-replay cache makes the second identical call cost **zero** upstream tokens.
2. **Cross-provider consistency** — one OpenAI-shaped pipe and one cache contract across OpenAI, Anthropic, Gemini, DeepSeek, Moonshot/Kimi, Z.ai/GLM, Qwen, and xAI/Grok (BYOK).
3. **Locality / latency** — cache GETs on the nearest Redis edge replica; pre-first-byte failover keeps the pipe honest.
4. **Replay / audit value** — every hit is an auditable identical-request replay with a readable meter; never a training corpus.

> Point any OpenAI-compatible client (or the Ohm Agent Shell) at one base URL.
> Keep your keys or use a managed pool. Gain prompt replay, compliant web
> context, SSO tenancy, and a clean ledger — a bill that rents the plumbing
> and governs the chaos, not a wholesale model invoice.

## Non-goals

- PAYG wholesale reseller of OpenAI/Anthropic tokens for Intermediate
- Semantic / fuzzy cache
- Treating Cursor Marketplace as existential distribution
