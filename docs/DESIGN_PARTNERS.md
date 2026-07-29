# Design-partner wedge

Target: **ten teams** with painful rate limits, duplicate cache middleware, or agents blocked on manual web browse.

Front door: [withohm.dev/design-partners](https://withohm.dev/design-partners) · `partners@withohm.dev`.

## Offer

- Complimentary **`design_partner`** plan (time-boxed; soft USD quota)
- In exchange: one public quote + measured improvements (before/after `/v1/usage`)

## Onboarding

1. Issue a key: `POST /v1/admin/tenants` with `plan=design_partner`, `label=<company>`, `terms_ack`/`dpa_ack`
2. Defaults: 90 days, soft quota from `AT_DESIGN_PARTNER_*` (override with body fields)
3. They set `base_url` to local `http://localhost:8081/v1` (or `https://api.withohm.dev/v1` after cutover) + Ohm `api_key`
4. BYOK: send provider key as `X-Ohm-Upstream-Key` on misses (see [QUICKSTART.md](QUICKSTART.md))
5. Optional: attach Ohm MCP in Cursor ([CURSOR.md](CURSOR.md))
6. After one week: export from `/v1/usage`:
   - `cache_hit_ratio`, `arbitrage_gross_usd`, `requests` (wait / miss-ratio relief)
   - `fetches`, `today_fetches`, web-context attach rate (`fetches / requests`)
7. Capture quote for the Ohm homepage social-proof section

## Mailbox / SPF

- Confirm `partners@withohm.dev` receives in M365
- Apex TXT SPF should include Outlook: `v=spf1 include:spf.protection.outlook.com -all` (or include both Outlook and GoDaddy if still sending via secureserver)

## Success signal

Named companies repeat the Ohm promise without a white paper — and show **both** cache hit-ratio / wait relief **and** non-zero web-context attach rate when browse is in scope.
