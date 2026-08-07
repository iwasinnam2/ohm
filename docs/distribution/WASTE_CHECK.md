# Waste-check campaign — operator runbook

Primary GTM for indie proof. Persona: **Cursor Pro+ user who hit usage max
~5 days in.** Benefit sentence:

> Your agent asked the same thing twice. Cursor billed you twice. withOhm
> answers the second from cache.

Funnel: homepage → `/demo` → MISS→HIT → mint `/r/…` → share → `/bounty` → `/i`.

**CTA doctrine:** hero = belief (waste check); header Start = conversion
(`/signup`); header Log in = return (`/login`). Named in [BRAND.md](../BRAND.md).

Enterprise chaos remains the thesis for directory / enterprise apply. Indie
surfaces lead with quota burn, then point at `/docs/enterprise-chaos`.

Related: [GAP_SURFACES.md](GAP_SURFACES.md) · [SHOW_HN_RUNBOOK.md](SHOW_HN_RUNBOOK.md) ·
[SIEGE_DEFENSE.md](SIEGE_DEFENSE.md) · [PARTNER_HIT_LIST.md](PARTNER_HIT_LIST.md) ·
[STEAL_KIT.md](STEAL_KIT.md) · [CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md) ·
[CARE_AUDIT.md](../CARE_AUDIT.md) (full-product care / SoT remediation)

---

## Success metrics (week 1)

- Incognito `/demo` works with no key paste (`OHM_DEMO_API_KEY` set)
- ≥20 demo miss→HIT sessions on proof tenant
- ≥5 public `/r/…` receipts
- Show HN — **blocked** (HN account banned); do not attempt
- cursor.directory submitted
- ≥10 partners `touched`, ≥2 `keyed`
- ≥1 bounty claim or steal-kit PR opened

---

## Manual ops (you only)

Agent does not post as you.

### B0 — Before the spike

1. Mint a **dedicated** public-proof tenant/key (Intermediate or design_partner).
   Do not reuse a personal paying key.
2. Set Amplify env `OHM_DEMO_API_KEY` on branch **master** (Hosting →
   Environment variables — not only “build” if the UI splits them). Save, then
   **Redeploy this version** / `start-job RELEASE`. Confirm:
   `curl -s https://www.withohm.dev/api/demo-session` → `"available": true`.
3. Incognito: open https://www.withohm.dev/demo → **Prove miss → HIT** → mint
   receipt → open `/r/…`.
4. API smoke:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey $env:OHM_API_KEY
```

5. Keep [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md) open for thread replies.
   **Show HN is out** — HN account banned; do not use [SHOW_HN_RUNBOOK.md](SHOW_HN_RUNBOOK.md).

### B1 — Distribution spike (no HN)

1. **cursor.directory** — chaos-governor packet
   ([CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md)); logo
   `ohm-icon-360.png`; cite T-E60068.
2. **Cursor Forum** — [GAP_SURFACES.md](GAP_SURFACES.md) §1; reply same day.
3. **r/cursor** — §2 (Pro+ burn + `/demo`).
4. **X thread** — §3; tag `@cursor_ai` only where factual.
5. **Steal-kit** — open 1–2 PRs ([STEAL_KIT.md](STEAL_KIT.md)).
6. Optional: r/SideProject (promo-tolerant) with waste-check link — distinct copy.

### B2 — Partners (ongoing, 5/day)

1. Replace `[fill]` rows in [partner_hit_list.csv](partner_hit_list.csv) with
   real handles (Reddit commenters, Forum pain posts, Pro+ limit complainers).
   The CSV is a **template** until then — do not count placeholders as pipeline.
2. DM offer: run `/demo` + design-partner key — not logo/PR.
3. Same-day mint ([PARTNER_ONBOARD.md](PARTNER_ONBOARD.md)); day 5–7 quote /
   receipt share for bounty.
4. Pay bounty claims at `partners@withohm.dev` when the email includes
   **receipt URL + social post URL + seat email** per [/bounty](https://www.withohm.dev/bounty)
   ($100 credit). Receipt alone does not qualify. Log evidence in
   [BOUNTY_EVIDENCE.md](BOUNTY_EVIDENCE.md).

### B3 — Do not

- Re-post identical floodgate copy to mcp / LLMDevs / AI_Agents
- Restore homepage aggregate savings counter
- Paid ads this sprint
- Cursor BD until ≥3 receipt-backed quotes ([CURSOR_BD_BRIEF.md](CURSOR_BD_BRIEF.md))
- Pitch “save Cursor COGS” / Anysphere partnership on directory listing
