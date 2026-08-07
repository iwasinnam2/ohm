# Waste-check campaign — operator runbook

Primary GTM for indie proof. Persona: **Cursor Pro+ user who hit usage max
~5 days in.** Benefit sentence:

> Your agent asked the same thing twice. Cursor billed you twice. withOhm
> answers the second from cache.

Funnel: homepage → `/demo` → MISS→HIT → mint `/r/…` → share → `/bounty` → `/i`.

Enterprise chaos remains the thesis for directory / enterprise apply. Indie
surfaces lead with quota burn, then point at `/docs/enterprise-chaos`.

Related: [GAP_SURFACES.md](GAP_SURFACES.md) · [SHOW_HN_RUNBOOK.md](SHOW_HN_RUNBOOK.md) ·
[SIEGE_DEFENSE.md](SIEGE_DEFENSE.md) · [PARTNER_HIT_LIST.md](PARTNER_HIT_LIST.md) ·
[STEAL_KIT.md](STEAL_KIT.md) · [CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md)

---

## Success metrics (week 1)

- Incognito `/demo` works with no key paste (`OHM_DEMO_API_KEY` set)
- ≥20 demo miss→HIT sessions on proof tenant
- ≥5 public `/r/…` receipts
- Show HN fired once with live coverage
- cursor.directory submitted
- ≥10 partners `touched`, ≥2 `keyed`
- ≥1 bounty claim or steal-kit PR opened

---

## Manual ops (you only)

Agent does not post as you.

### B0 — Before Show HN (day of or day before)

1. Mint a **dedicated** public-proof tenant/key (Intermediate or design_partner).
   Do not reuse a personal paying key.
2. Set Amplify env `OHM_DEMO_API_KEY` to that key; wait for RELEASE green.
3. Incognito: open https://www.withohm.dev/demo → **Prove miss → HIT** → mint
   receipt → open `/r/…`.
4. API smoke:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey $env:OHM_API_KEY
```

5. Paste Show HN first comment ([SHOW_HN_RUNBOOK.md](SHOW_HN_RUNBOOK.md)) + keep
   [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md) open.

### B1 — Distribution spike (Tue–Thu 13:00–15:00 UK for HN)

1. **Show HN** — URL = GitHub repo; first comment within 60s leads with
   `https://www.withohm.dev/demo`; guard ≥2h replies.
2. **cursor.directory** — chaos-governor packet
   ([CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md)); logo
   `ohm-icon-360.png`; cite T-E60068.
3. **Cursor Forum** — [GAP_SURFACES.md](GAP_SURFACES.md) §1; reply same day.
4. **r/cursor** — §2 (Pro+ burn + `/demo`).
5. **X thread** — §3; tag `@cursor_ai` only where factual.
6. **Steal-kit** — open 1–2 PRs ([STEAL_KIT.md](STEAL_KIT.md)).

### B2 — Partners (ongoing, 5/day)

1. Replace `[fill]` rows in [partner_hit_list.csv](partner_hit_list.csv) with
   real handles (Reddit commenters, Forum pain posts, Pro+ limit complainers).
2. DM offer: run `/demo` + design-partner key — not logo/PR.
3. Same-day mint ([PARTNER_ONBOARD.md](PARTNER_ONBOARD.md)); day 5–7 quote /
   receipt share for bounty.
4. Pay bounty claims at `partners@withohm.dev` when receipts are public.

### B3 — Do not

- Re-post identical floodgate copy to mcp / LLMDevs / AI_Agents
- Restore homepage aggregate savings counter
- Paid ads this sprint
- Cursor BD until ≥3 receipt-backed quotes ([CURSOR_BD_BRIEF.md](CURSOR_BD_BRIEF.md))
- Pitch “save Cursor COGS” / Anysphere partnership on directory listing
