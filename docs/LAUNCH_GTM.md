# Launch GTM — Cursor marketplace (from zero partners)

You do **not** need a warm list of 10 companies. Treat “10 design partners” as a **quota you fill by fishing in public Cursor-native waters**, not a Rolodex you already own.

## Strategy (locked)

1. Fix install defaults so marketplace browsers hit `https://api.withohm.dev/v1`.
2. Open a public apply funnel at [withohm.dev/design-partners](https://withohm.dev/design-partners).
3. Spend 30–45 min/day for two weeks on **cold, personal outreach** in Cursor-native places (templates below).
4. Ship one demo post + cursor.directory + polished Marketplace listing.
5. Defer generic webdev forums and paid ads until 3+ people have used the pipe.

Full channel ladder: [BRAND.md](BRAND.md). Partner ops: [DESIGN_PARTNERS.md](DESIGN_PARTNERS.md). Copy/paste scripts: [OUTREACH_TEMPLATES.md](OUTREACH_TEMPLATES.md). Listings: [listings/](listings/).

## How to get 10 partners with nobody in mind

### Mindset

Each “partner” can be a solo Cursor power user. Indie counts. Goal is **named humans who attach MCP + give a quote**, not Fortune 500 BD.

### Daily fishing loop (repeat until n=10)

| Step | Action | Where |
|------|--------|--------|
| 1 | Search people who posted about MCP, agent browse, rate limits, or “Cursor tools” in the last 7 days | Cursor Forum, Discord (Cursor / MCP), X/Twitter |
| 2 | Reply helpfully to **their** problem in one sentence, then offer a free 90-day design-partner seat | Same thread / DM |
| 3 | Point them to `/design-partners` apply (or issue a key the same day if they DM) | withohm.dev |
| 4 | After they run one fetch + one chat: ask for a one-line quote + `/v1/usage` screenshot | Email / Discord |

**Quota math:** ~5 genuine outreaches/day × 14 days = 70 touches. At a conservative 15% reply and 50% of replies converting → **~5 partners**. Double the weeks or touches to hit 10. This is grinding, not magic.

### Where strangers hang out (priority order)

1. **[Cursor Forum](https://forum.cursor.com)** — MCP / Tips threads; one launch post + reply to others
2. **Cursor Discord / MCP Discords** — #showcase, #mcp, #plugins (follow each server’s promo rules)
3. **[cursor.directory](https://cursor.directory)** — listing; inbound from people browsing MCP catalogs
4. **X/Twitter** — search `Cursor MCP`, `ohm_fetch`, “agent browser”, “prompt cache”; reply, don’t cold-spam DMs first
5. **GitHub** — issues/Discussions on popular MCP/agent repos: helpful fix first, soft mention second
6. **HN “Show HN” / Lobsters** — only after a 60s demo GIF and public API smoke; one post, not a campaign

**Skip for launch:** r/webdev, generic “AI tools” Facebook groups, unsolicited LinkedIn InMail blasts.

### Inbound (works while you sleep)

- Marketplace + cursor.directory listing → Checkout → deeplink
- `/design-partners` form → `partners@` / `admin@` via Resend
- Intermediate trial ($0 membership + card) for people who won’t “apply”

You can run Intermediate self-serve **in parallel** with design partners. Partners are for **quotes + feedback**; Intermediate is for revenue.

## Week plan

| Day | Ship / do |
|-----|-----------|
| 0 | Confirm `api.withohm.dev` smoke; plugin default URL = production; listing docs live |
| 1 | Submit/update cursor.directory; polish Marketplace description |
| 1–14 | Daily fishing loop; log outreaches in a simple sheet (name, channel, date, status) |
| 3 | Post Cursor Forum launch (template in OUTREACH_TEMPLATES) |
| 7 | First partner check-in; capture first quote for homepage |
| 14 | Retarget: anyone who clicked but didn’t attach; ask what blocked them |

## Success signals

- ≥3 design-partner keys issued (even solo)
- ≥1 public quote on the homepage
- Marketplace/listing traffic that completes Checkout without a human DM
- Non-zero `ohm_web_fetch` + cache hits on partner `/v1/usage`

## What this repo now includes

| Asset | Path |
|-------|------|
| This plan | [LAUNCH_GTM.md](LAUNCH_GTM.md) |
| Partner ops + sourcing | [DESIGN_PARTNERS.md](DESIGN_PARTNERS.md) |
| Cold copy | [OUTREACH_TEMPLATES.md](OUTREACH_TEMPLATES.md) |
| Marketplace listing draft | [listings/MARKETPLACE.md](listings/MARKETPLACE.md) |
| cursor.directory draft | [listings/CURSOR_DIRECTORY.md](listings/CURSOR_DIRECTORY.md) |
| Public apply | https://withohm.dev/design-partners |
