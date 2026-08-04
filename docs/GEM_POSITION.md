# Gem position — withOhm

Canonical wedge for product and GTM. Enterprise framing: [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md).

## The inefficiency

Agent products scale context across consecutive turns: tool results, retrieved
files, compacted history. Naive routing **re-pays prefill** on every call.
Compaction is a pressure valve — it does not remove waste from identical or
near-mechanical repeats (retries, loops, CI prompt suites).

## The gem

withOhm is the **tollbooth on wasted and repeated inference**, embedded in a
broader **chaos governor** (SSO, compliance, clean ledger, Agent Shell):

| Layer | Role |
|-------|------|
| Labs | Generation + model billing (BYOK or managed pool) |
| Any client | Cockpit (Agent Shell, custom apps, optional Cursor/VS Code) |
| **withOhm** | Metered pipe + governance: replay, compliant ingest, ledger |

We do **not** sell bigger context windows or wholesale tokens on Intermediate.
We rent plumbing that makes context scaling economically survivable — and
make enterprise AI spend **governable**.

## Promise

> Point any OpenAI-compatible client (or the Ohm Agent Shell) at one base URL.
> Keep your keys or use a managed pool. Gain prompt replay, compliant web
> context, and a clean ledger — rent the plumbing, govern the chaos.

## Path inventory + spend caps

Tag traffic with `X-Ohm-Path` (docs-bot, ci-prompts, support-triage, …). Hit-ratio
APIs and the org console inventarize frequency farms; org spend caps soft-stop or
hard-block MISS flood so the spread (provider avoided − pipe rent) is protected
without overclaiming a savings SLA.

## Dual savings + clean ledger

`GET /v1/savings` / receipts:

| Field | Meaning |
|-------|---------|
| `estimated_provider_avoided_usd` | Hit tokens × blended provider list rate |
| `pipe_rent_usd` | What Ohm metered |
| `roi_ratio` | Provider avoided ÷ pipe rent |
| `estimate_only` | Always true on blended estimates |

Org FinOps export (`GET /v1/org/ledger/export`) attributes immutable usage
events by **cost center** — the corporate clean ledger.

## Non-goals

- Semantic / fuzzy cache
- PAYG reseller of lab tokens on Intermediate
- Guaranteed savings SLAs
- Cursor Marketplace as the company thesis

## Distribution (priority order)

1. Enterprise apply + Agent Shell demo + OpenAI-compatible ingress  
2. Indie / design-partner proof of meter  
3. Optional MCP / directory listings (compatibility)

Vision: [VISION.md](VISION.md). Pricing: [PRICING.md](PRICING.md).
