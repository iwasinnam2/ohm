# Design-partner wedge (from zero)

Target: **ten teams or solo Cursor power users** with painful rate limits, duplicate cache middleware, or agents blocked on manual web browse.

**You do not need anyone “in mind.”** Fill the quota with cold fishing — see [LAUNCH_GTM.md](LAUNCH_GTM.md) and [OUTREACH_TEMPLATES.md](OUTREACH_TEMPLATES.md).

Front door: [withohm.dev/design-partners](https://withohm.dev/design-partners) · `partners@withohm.dev`

## Offer

- Complimentary **`design_partner`** plan (time-boxed; soft USD quota)
- In exchange: one public quote + measured improvements (before/after `/v1/usage`)

## Sourcing when you have no network

1. **Inbound:** leave the apply form live; share the URL everywhere you post.
2. **Outbound:** 5 personal outreaches/day in Cursor Forum / Discord / X (templates ready).
3. **Self-serve fallback:** anyone who won’t “partner” still starts Intermediate trial — count them as pipeline, not quotes.
4. **Log touches** so you don’t ghost people who replied.

Ideal first 10 mix: ~7 indies + ~3 small teams. Logos are nice; **quotes that name the pain** matter more.

## Onboarding

1. Application hits Resend → `admin@withohm.dev` (reply-to = applicant), **or** you issue directly after a DM.
2. Issue a key: `POST /v1/admin/tenants` with `plan=design_partner`, `label=<company_or_handle>`, `terms_ack`/`dpa_ack`
3. Defaults: 90 days, soft quota from `AT_DESIGN_PARTNER_*` (override with body fields)
4. They set `OHM_BASE_URL=https://api.withohm.dev/v1` + Ohm `api_key` (local `:8081` only for your own smoke)
5. BYOK: provider key as `OHM_UPSTREAM_KEY` / `X-Ohm-Upstream-Key` on misses
6. Attach Ohm MCP in Cursor ([CURSOR.md](CURSOR.md)) — success-screen deeplink after Intermediate Checkout also works
7. After one week: export from `/v1/usage`:
   - `cache_hit_ratio`, `arbitrage_gross_usd`, `requests`
   - `fetches`, `today_fetches`, web-context attach rate (`fetches / requests`)
8. Capture quote for the Ohm homepage social-proof section

## Mailbox / SPF

- Confirm `partners@withohm.dev` receives in M365
- Apex TXT SPF should include Outlook: `v=spf1 include:spf.protection.outlook.com -all`

## Success signal

Named humans (solo ok) repeat the Ohm promise without a white paper — and show **both** cache hit-ratio / wait relief **and** non-zero web-context attach rate when browse is in scope.
