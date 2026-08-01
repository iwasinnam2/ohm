# Design-partner onboard — same-day key + day 5–7 quote

Canonical product doc: [DESIGN_PARTNERS.md](../DESIGN_PARTNERS.md).  
Hit list: [PARTNER_HIT_LIST.md](PARTNER_HIT_LIST.md).

---

## When they say yes

Friction kills partners. Issue the key **the same day**.

### 1. Mint seat

Requires admin token (`AT_ADMIN_TOKEN` / ops secret used by `POST /v1/admin/tenants`).

```powershell
.\scripts\issue_design_partner.ps1 -Label "acme-jane" -PartnerDays 90 -AdminKey $env:AT_ADMIN_API_KEY
```

Or curl:

```bash
curl -s https://api.withohm.dev/v1/admin/tenants \
  -H "Authorization: Bearer $AT_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"plan":"design_partner","label":"acme-jane","terms_ack":true,"dpa_ack":true,"partner_days":90}'
```

Response includes `api_key` **once** — store it, send to them securely, never commit it.

Update CSV: `status=keyed`, `key_issued=y`.

### 2. Send attach instructions

```text
Key issued (store it — we can't show it again).

Attach (≈2 min): https://www.withohm.dev/i
Docs: https://www.withohm.dev/docs/cursor

Env:
  OHM_BASE_URL=https://api.withohm.dev/v1
  OHM_API_KEY=<the key>
  OHM_UPSTREAM_KEY=<your OpenAI/Anthropic key for cache misses>

Quick check after a few calls: ohm_usage in Cursor, or GET /v1/usage

I'll ping in about a week for one public sentence + a usage snapshot —
that's the whole founding ask. Happy to debug attach anytime.
```

### 3. They attach

Success = MCP tools visible + at least one `ohm_chat` or `ohm_fetch_web` call + non-empty `/v1/usage`.

---

## Day 0 — baseline (optional but strong)

Before habits change, ask for a paste of `GET /v1/usage` (or `ohm_usage`) so
day 5–7 can show before/after hit ratio.

## Day 5–7 — quote ask

From [OUTREACH_TEMPLATES.md](../OUTREACH_TEMPLATES.md) §6 — prefer dual-ledger proof:

```text
Glad you’re on the pipe. Three asks when you have 2 minutes:

1) One sentence I can put on withohm.dev (name + optional company) —
   ideal if it mentions duplicate agent calls / rate limits / browse friction
2) Paste of GET /v1/savings (provider avoided + pipe_rent + roi_ratio) and/or /v1/usage
3) Optional: mint a public receipt (ohm_receipt) for a README badge

In exchange I’ll keep the design-partner window clear of meters for the
remaining days. Thanks!
```

**Proof bar (gem scaffold):** hit ratio > 0, dual-ledger numbers present,
quote names a real pain. Prefer ROI that screenshots cleanly.

When captured:

- [ ] Paste quote into homepage social-proof section (site content)
- [ ] CSV: `quote_captured=y`, `status=quoted`
- [ ] Savings receipt badge ([STEAL_KIT.md](STEAL_KIT.md)) when they agree
- [ ] Log `roi_ratio` + `estimated_provider_avoided_usd` for Cursor BD pack

Never ask for a logo before they’ve used the pipe.

---

## Escape hatch

If they won’t partner: Intermediate self-serve at https://www.withohm.dev — count as pipeline, not quote.

---

## Done when

- [ ] Same-day mint path verified (`issue_design_partner.ps1` or curl)
- [ ] Attach blurb ready to paste
- [ ] Quote ask calendar/reminder habit for day 5–7 after each key
