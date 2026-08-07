# Design-partner hit list — 20 rows, 5 outreaches/day

Tracking file: [partner_hit_list.csv](partner_hit_list.csv)

Front door: https://www.withohm.dev/design-partners · `partners@withohm.dev`

Offer: 90-day `design_partner` seat (BYOK) for one public sentence + `/v1/usage` snapshot after a week. See [PARTNER_ONBOARD.md](PARTNER_ONBOARD.md).

---

## Columns

| Column | Meaning |
|--------|---------|
| `company_or_handle` | Org or public handle |
| `pain_observed` | Their words — duplicate calls, browse blocked, robots/PII, LLM bill |
| `source_link` | Thread, job, blog, product page where you saw the pain |
| `person` | Named eng who can say yes (not `info@`) |
| `channel` | `forum_dm` / `x_dm` / `discord` / `email` / `reddit_dm` |
| `research_urls` | Public about/product/careers URLs for JSON research (pipe-separated) |
| `personalization_hook` | One sentence proving you read them |
| `status` | `queued` → `touched` → `replied` → `keyed` → `quoted` / `passed` |
| `date_touched` | ISO date of last outreach |
| `replied` / `key_issued` / `quote_captured` | `y` / `n` |
| `notes` | Anything else |

---

## How to fill 20 rows (sourcing order)

Do **not** invent contacts. Fill from real public signals:

1. **Warm from your threads** — commenters on r/mcp, r/LLMDevs, r/AI_Agents (and r/cursor once live) who stated a real problem.
2. **Pain posts that aren’t yours** — Cursor Forum, Discord, X: duplicate prompts, agent browse, robots.txt, MCP fetch.
3. **Product-shaped companies** — agent/research-copilot/Cursor-heavy startups; find the eng who posts.
4. **Cold email last** — public work email + cited pain only ([OUTREACH_TEMPLATES.md](../OUTREACH_TEMPLATES.md) §5).

Ideal mix: ~7 indies + ~3 small teams among the first 10 who convert; keep 20 in the pipeline.

### Suggested research seeds (URLs only — you still find the person)

Use these *categories* to hunt candidates; add concrete handles when you find them:

| Seed type | Where to look | Likely pain |
|-----------|---------------|-------------|
| Cursor Forum MCP threads | forum.cursor.com | Attach / browse / rate limits |
| HN Who’s Hiring (agent / LLM infra) | news.ycombinator.com | Building agents, token cost |
| YC / startup directories mentioning agents | company sites + careers | Agent loops, research fetch |
| Awesome-MCP / agent framework issues | GitHub | Need compliant browse |
| Your own Show HN / Reddit commenters | after they post | Exact-match / cache skepticism → convert to trial |

Optional personalization: run [scripts/partner_research_fetch.ps1](../../scripts/partner_research_fetch.ps1) on `research_urls` (see [PARTNER_JSON_RESEARCH.md](PARTNER_JSON_RESEARCH.md)). Never use Ohm to harvest emails.

---

## Daily cadence

1. Open the CSV; ensure ≥20 rows with `status=queued` or in flight.
2. Send **5 personalized** outreaches (message skeleton below).
3. Set `status=touched`, `date_touched=today`.
4. Same-day key if they say yes → [PARTNER_ONBOARD.md](PARTNER_ONBOARD.md).
5. Show HN is **BLOCKED** (HN account banned) — do not attempt. Pause cold
   spray only when a live public thread needs replies that day.

---

## Message skeleton (companies / solos)

```text
{Name} — saw {specific thing: thread / product / post about X}.

That’s the exact failure mode withOhm is built for: {cache replay for identical agent calls / robots+PII-safe fetch}. BYOK — your provider keys stay yours.

I’m opening a few founding design-partner seats: 90 days free on the pipe in exchange for one public sentence after a week and a quick /v1/usage snapshot (hit ratio / fetches). No deck, no call required.

Apply: https://www.withohm.dev/design-partners
Or reply “key” and I’ll issue one to this address.

If timing’s wrong, Intermediate is self-serve on the same site.
```

Tone: peer, not vendor. Never say “PR boost.” Say “founding quote” or “one public sentence.”

Shorter variants: [OUTREACH_TEMPLATES.md](../OUTREACH_TEMPLATES.md) §2–5.

---

## Done when

- [ ] CSV has 20 real rows (person + pain + channel)
- [ ] 5/day cadence running until ~10 partners keyed or pipeline full
- [ ] Each keyed partner scheduled for day 5–7 quote ask
