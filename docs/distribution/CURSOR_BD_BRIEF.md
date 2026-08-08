# Cursor / Anysphere BD brief — withOhm

> **Status:** Optional compatibility channel. Company thesis is enterprise
> chaos governance ([ENTERPRISE_CHAOS.md](../ENTERPRISE_CHAOS.md)) — Cursor
> is not required for distribution or product legitimacy.

**Audience:** Cursor Marketplace reviewers, partnerships, agent-infra.  
**Ask:** Feature/list withOhm as an optional MCP client.  
**Not asking:** Replace Composer billing, wholesale our tokens, or native embed on day one.

Companion: [GEM_POSITION.md](../GEM_POSITION.md) · Marketplace draft: [../listings/MARKETPLACE.md](../listings/MARKETPLACE.md)

---

## Problem (platform economics)

Agent loops in Cursor amplify **repeat prefill**: retries, tool cycles, stable
system+file pairs, and — the dominant pattern — every turn resending the
entire growing transcript, so cost scales combinatorially with conversation
length. Users hit compaction rituals and bill shock. Cursor bears
support/churn gravity when agent spend feels opaque or wasteful. Building
billing-grade cache + robots-aware browse in-house is real engineering and
compliance surface.

## What withOhm is

OpenAI-compatible **ingress pipe** attachable via local stdio MCP
(`pip install withohm-mcp`) or base URL:

- **Exact-match Redis prompt replay** — identical agent calls replay without
  re-billing the provider; hits are metered (~$2/M) so incentives stay honest
- **Breakpoint autopilot** — auto-places Anthropic `cache_control` prefix
  breakpoints on the longest byte-stable prefix of a growing conversation, so
  naive clients that resend the whole transcript every turn (Cursor's own
  pattern) still get provider-side prefill discounting without placing a
  breakpoint themselves ([CACHE_AUTOPILOT.md](../CACHE_AUTOPILOT.md))
- **BYOK** — user/Cursor keeps the model relationship; Ohm does not float
  wholesale tokens on Intermediate, and never stores the upstream key
- **Compliant public web fetch** — purpose-bound, robots-gated, PII-redacted
  context for agents (`ohm_fetch_web`)
- **Triple savings ledger** — `GET /v1/savings` shows estimated provider $
  avoided (Ohm's own replay HITs), estimated provider-cache savings
  (breakpoint autopilot), and Ohm pipe rent + `roi_ratio` (estimates labeled
  `estimate_only`)

Site: https://www.withohm.dev · API: https://api.withohm.dev/v1  
Repo: https://github.com/iwasinnam2/ohm · Privacy: https://www.withohm.dev/docs/privacy

## Why this helps Cursor (not just end users)

| User win | Cursor-adjacent win |
|----------|---------------------|
| Lower duplicate upstream spend on mechanical agent traffic | Happier power users; clearer “agent bill” story |
| Compliant browse without DIY scrapers | Less shady fetch tooling in the ecosystem |
| Public savings receipts / badges | Social proof that Cursor + Ohm workflows work |

Cursor keeps model billing. Ohm rents cache + compliant browse — aligned with
[VISION.md](../VISION.md).

## Proof to attach (when sending)

1. Live Marketplace listing + https://www.withohm.dev/i install path  
2. Sample `GET /v1/savings` JSON (dual ledger + `roi_ratio`)  
3. 1–3 public savings receipts (badges) from design partners  
4. This brief + [GEM_POSITION.md](../GEM_POSITION.md)

## Single ask

1. **Marketplace:** approve/refresh the withOhm listing (employee review welcome —
   see submission notes in MARKETPLACE.md).  
2. **Pilot:** intro to the right owner for a non-exclusive design-partner
   conversation (Marketplace feature, docs mention, or agent-infra feedback).

Contact: `partners@withohm.dev`

---

## Architecture (one paragraph)

Client → Rust edge (`:8081`) → Redis exact-match lookup → on miss, Python
control plane (`:8080`) → BYOK upstream (OpenAI/Anthropic) or mock. Web ingest
is a separate purpose-limited worker. Edge HIT metering via
`POST /internal/edge-hit`. Legal bounds: [LEGAL.md](../LEGAL.md).

## Sample savings shape

```json
{
  "cache_hit_ratio": 0.42,
  "estimated_provider_avoided_usd": 12.6,
  "provider_cache_read_tokens": 48000,
  "estimated_provider_cache_savings_usd": 0.65,
  "pipe_rent_usd": 0.85,
  "roi_ratio": 14.8,
  "estimate_only": true
}
```

Blended provider rate defaults to $15/M tokens (`AT_PROVIDER_AVOIDED_PER_1K_TOKENS`);
always an estimate, never a guarantee. `estimated_provider_cache_savings_usd`
is a distinct rail (never summed with `estimated_provider_avoided_usd`) —
it only fires when the breakpoint autopilot got the upstream provider itself
to discount part of a MISS.
