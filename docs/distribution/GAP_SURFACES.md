# Gap surfaces — fire-ready (post these; do not re-flood)

**Already shipped — do not re-post identical launch copy:**

- r/mcp
- r/LLMDevs
- r/AI_Agents

**Still open (this pack):**

| Surface | Status | Action |
|---------|--------|--------|
| Cursor Forum | Open | Post §1 below |
| **Marketplace refresh** | Open | [MARKETPLACE.md](../listings/MARKETPLACE.md) — employee review notes |
| **cursor.directory (primary)** | Open | Chaos-governor packet — [CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md) |
| r/cursor | Open | Post §2 (distinct copy) |
| X thread | Open | Post §3 |
| Steal-kit list PRs | Open | Open 1–2 PRs from [STEAL_KIT.md](STEAL_KIT.md) |
| Show HN | Open | [SHOW_HN_RUNBOOK.md](SHOW_HN_RUNBOOK.md) |
| Cursor BD | After proof | [CURSOR_BD_BRIEF.md](CURSOR_BD_BRIEF.md) |

Warm reply-fishing under *other people’s* pain posts is always open — use [OUTREACH_TEMPLATES.md](../OUTREACH_TEMPLATES.md) §2–4.

---

## 1. Cursor Forum — launch post

**Where:** https://forum.cursor.com (MCP / plugins / showcase category as appropriate)

**Title:**

```text
withOhm — cut repeat agent prefill waste (prompt replay + compliant fetch, BYOK)
```

**Body:**

```text
Hey — shipped an MCP for Cursor that rents the pipe, not the model.
Agent loops re-pay the same prefill; we replay identical calls from Redis.

• ohm_chat — OpenAI-compatible ingress with Redis prompt replay
• ohm_fetch_web — purpose-bound public URL → markdown/JSON for agents
• ohm_savings — dual ledger: estimated provider $ avoided vs pipe rent + ROI
• ohm_usage — hit ratio + fetch meters

BYOK (your OpenAI/Anthropic key). Intermediate is $0 membership + usage meters.

I’m looking for ~10 founding design partners (solo ok): 90 days complimentary
in exchange for one public quote + a /v1/usage before/after.

Install / apply: https://www.withohm.dev/design-partners
Docs: https://www.withohm.dev/docs/cursor
Two-minute attach: https://www.withohm.dev/i
Marketplace: search “ohm” in Cursor plugins / MCP (works today without marketplace)

Happy to debug attach issues in-thread.
```

**After post:** paste the thread URL into [partner_hit_list.csv](partner_hit_list.csv) as an inbound source; reply to every attach question same day.

---

## 2. r/cursor — workflow post (distinct from floodgate)

**Title:**

```text
I built a Cursor plugin that gives the agent compliant web fetch and replays repeated LLM calls from cache
```

**Body:**

```text
Disclosure: my project. Plugin is in marketplace review; it works today
without the marketplace.

The itch: Cursor agents doing research re-fetch the same pages over and over,
and the raw fetches ignore robots.txt and happily paste PII into context.

withOhm sits between the agent and the web/provider. Fetches go through a
compliance pipe (robots respected, PII redacted, SSRF-safe). Identical chat
calls get replayed from Redis instead of being re-billed by the provider.

Setup is pip install withohm-mcp plus an mcp.json entry — two minutes:
https://www.withohm.dev/i

Founding design-partner seats (90 days free for one public sentence + a
/v1/usage snapshot): https://www.withohm.dev/design-partners

The skills are the part I most want feedback on: they teach the agent when
to reach for the pipe on its own. If it grabs the wrong tool, say so —
that's a skill-wording bug and cheap to fix.

Repo (MIT): https://github.com/iwasinnam2/ohm
```

---

## 3. X thread

Post from the personal account. Tag `@cursor_ai` only in tweet 6 where factual.

```text
1/ Shipped: withOhm — a metered pipe for AI agents.

Identical LLM calls replay from cache instead of being re-billed. Web fetches
come back robots-respecting and PII-redacted. MIT repo, live today.

https://www.withohm.dev

2/ The observation it's built on: agents are mechanical. Retries and research
loops produce byte-identical requests at rates human users never do. Every
one of those is currently billed at full token price. That's rent nobody
should be paying twice.

3/ The unfashionable choice: exact-match caching, not semantic. "Almost the
same prompt" is not the same prompt — serving a near-miss from cache is how
you turn a savings feature into a refunds feature.

4/ Compliant fetch is the other half. robots.txt consulted at fetch time, PII
redacted before content reaches the model, SSRF blocked at connect time.
The agent asks for a URL; what returns is safe to put in context.

5/ Architecture: a cache hit is a billable event, so the hit path is built
to billing-grade reliability — served from Redis, metered idempotently
before the response leaves. Never best-effort.

6/ It's an MCP server, so @cursor_ai and Claude agents get it as native tools:
pip install withohm-mcp. Plugin is in marketplace review; works today
without it. Install: https://www.withohm.dev/i

7/ $0 to connect, priced per use. Founding design partners (90d free for one
public sentence): https://www.withohm.dev/design-partners
Repo: https://github.com/iwasinnam2/ohm
```

---

## 4. cursor.directory (primary — support deferred marketplace here)

Submit / update using the **chaos governor** packet in
[CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md) — not the old
Cursor-MCP trojan one-liner.

Checklist:

- [ ] Title/one-liner lead with control plane / chaos governor (Cursor optional)
- [ ] Links: site, `/docs/enterprise-chaos`, `/workbench`, `/org`, `/i`, GitHub
- [ ] Publisher note cites ticket T-E60068 → directory
- [ ] Record submit date in partner hit list notes

---

## 5. Steal-kit PRs (1–2 this sprint)

From [STEAL_KIT.md](STEAL_KIT.md):

1. `punkpeye/awesome-mcp-servers` — add withOhm row
2. Any second list/directory that accepts MCP entries

Do not pitch; contribute a dependency line.

---

## Done when

- [ ] Cursor Forum live
- [ ] cursor.directory submitted
- [ ] r/cursor posted (optional but recommended before Show HN)
- [ ] X thread posted
- [ ] ≥1 steal-kit PR opened
