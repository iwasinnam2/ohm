# Gem position — withOhm

Canonical wedge for product and GTM. Enterprise framing: [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

**Dual audience:** indie / Cursor surfaces lead with **waste check** (prefill
replay proof → Intermediate). Directory / enterprise lead with **chaos
governor**. CTA doctrine: [BRAND.md](BRAND.md).

## The inefficiency

Agent products scale context across consecutive turns: tool results, retrieved
files, compacted history. Naive routing **re-pays prefill** on every call.
Compaction is a pressure valve — it does not remove waste from identical or
near-mechanical repeats (retries, loops, CI prompt suites).

Cursor-style IDE agents are the sharpest case: every turn resends the
**entire growing transcript**, so cost scales combinatorially with
conversation length even when nothing else changed. Provider-native prompt
caching (Anthropic `cache_control`, OpenAI automatic caching) exists to fix
exactly this — but only if a breakpoint lands on the right block, inside the
lookback window, before the TTL expires. Naive clients place it wrong or not
at all. See [CACHE_AUTOPILOT.md](CACHE_AUTOPILOT.md).

## The gem

withOhm is the **metered pipe on wasted and repeated inference** (tollbooth
synonym), embedded in a broader **chaos governor** (SSO, compliance, clean
ledger, Agent Shell):

| Layer | Role |
|-------|------|
| Labs | Generation + model billing (BYOK or managed pool) |
| Any client | Cockpit (Agent Shell, custom apps, optional Cursor/VS Code) |
| **withOhm** | Metered pipe + governance: replay, compliant ingest, ledger |

We do **not** sell bigger context windows or wholesale tokens on Intermediate.
We rent plumbing that makes context scaling economically survivable — and
make enterprise AI spend **governable**.

Two exact-match mechanisms, one philosophy, different granularity:
**whole-request replay** ([CACHE_TREES.md](CACHE_TREES.md)) skips the call
entirely on a byte-identical repeat; the **breakpoint autopilot**
([CACHE_AUTOPILOT.md](CACHE_AUTOPILOT.md)) engineers the provider's own
prefix discount correctly when the request isn't identical but its prefix
is — Ohm no longer only *contrasts* itself with provider-native caching, it
also *correctly places it* on the customer's behalf.

## Promise

> Point any OpenAI-compatible client (or the Ohm Agent Shell) at one base URL.
> Keep your keys or use a managed pool. Gain prompt replay, compliant web
> context, and a clean ledger — rent the plumbing, govern the chaos.

## Path inventory + spend caps

Tag traffic with `X-Ohm-Path` (docs-bot, ci-prompts, support-triage, …). Hit-ratio
APIs and the org console inventarize frequency farms; org spend caps soft-stop or
hard-block MISS flood so the spread (provider avoided − pipe rent) is protected
without overclaiming a savings SLA.

## Triple savings + clean ledger

`GET /v1/savings` / receipts — three independent rails, never summed:

| Field | Meaning |
|-------|---------|
| `estimated_provider_avoided_usd` | Ohm's own exact-replay HITs × blended provider list rate — the call never happened |
| `estimated_provider_cache_savings_usd` | Breakpoint-autopilot MISSes where the *provider's own* cache discounted part of the call ([CACHE_AUTOPILOT.md](CACHE_AUTOPILOT.md)) |
| `pipe_rent_usd` | What Ohm metered |
| `roi_ratio` | Provider avoided ÷ pipe rent |
| `estimate_only` | Always true on blended estimates |

Org FinOps export (`GET /v1/org/ledger/export`) attributes immutable usage
events by **cost center** — the corporate clean ledger.

## Non-goals

- Semantic / fuzzy cache — including the breakpoint autopilot: every
  placement decision is a sha256 digest-equality check over normalized
  request units, never embeddings or similarity scoring. Exact-match applied
  at finer (prefix) granularity than "the whole request" is explicitly
  in-bounds; it is not a reversal of this non-goal. See [CACHE_AUTOPILOT.md](CACHE_AUTOPILOT.md) non-goals.
- PAYG reseller of lab tokens on Intermediate
- Guaranteed savings SLAs
- Cursor Marketplace as the company thesis

## Distribution (priority order)

1. Enterprise apply + Agent Shell demo + OpenAI-compatible ingress  
2. Indie / design-partner proof of meter  
3. Optional MCP / directory listings (compatibility)

Vision: [VISION.md](VISION.md). Pricing: [PRICING.md](PRICING.md).
