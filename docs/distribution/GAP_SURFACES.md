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

Primary campaign: [WASTE_CHECK.md](WASTE_CHECK.md) — every surface below ends on `/demo`.

---

## 1. Cursor Forum — launch post

**Where:** https://forum.cursor.com (MCP / plugins / showcase category as appropriate)

**Title:**

```text
Waste check: identical agent call twice — MISS then HIT (stop re-buying loops)
```

**Body:**

```text
Hey — if you’ve burned through Cursor Pro+ mid-month on agent loops, this is
the pattern: retries and research re-fetches re-issue byte-identical calls and
you pay for every one.

I shipped withOhm — an OpenAI-compatible pipe with exact-match Redis replay.
Identical requests: first MISS (upstream), second HIT (replay, no upstream
tokens). BYOK. MCP attach for Cursor in about two minutes.

Sixty-second proof (no pitch deck):
https://www.withohm.dev/demo

• ohm_chat — cached OpenAI-compatible ingress
• ohm_fetch_web — robots/PII/SSRF-safe public URL → markdown
• ohm_savings — dual ledger (provider avoided vs pipe rent)
• Install: https://www.withohm.dev/i
• $0 Intermediate seat: https://www.withohm.dev/billing/intermediate
• Teams / control plane: https://www.withohm.dev/docs/enterprise-chaos

Founding design partners (90 days free for one public sentence + /v1/usage):
https://www.withohm.dev/design-partners

Happy to debug attach issues in-thread.
```

**After post:** paste the thread URL into [partner_hit_list.csv](partner_hit_list.csv) as an inbound source; reply to every attach question same day.

---

## 2. r/cursor — workflow post (distinct from floodgate)

**Title:**

```text
Hit Cursor Pro+ mid-month? I built a pipe that replays identical agent calls from cache
```

**Body:**

```text
Disclosure: my project.

The itch: agent loops — retries, research, the same prompt suite — re-buy the
same tokens until the Pro+ meter is gone. Raw fetches ignore robots.txt and
paste PII into context.

withOhm sits on the path: exact-match replay (MISS then HIT) + compliant
fetch. One-click waste check:

https://www.withohm.dev/demo

Attach MCP (two minutes): https://www.withohm.dev/i
$0 seat: https://www.withohm.dev/billing/intermediate
Founding design partners (90d free): https://www.withohm.dev/design-partners

Skills teach the agent when to reach for the pipe. If it grabs the wrong
tool, say so — that’s a skill-wording bug and cheap to fix.

Repo (MIT): https://github.com/iwasinnam2/ohm
```

---

## 3. X thread

Post from the personal account. Tag `@cursor_ai` only in tweet 6 where factual.

```text
1/ Hit Cursor Pro+ mid-month? Your agent probably asked the same thing twice
and you paid twice.

Waste check (60s): https://www.withohm.dev/demo
Identical call → MISS then HIT. Second call does not re-buy the model.

2/ Agents are mechanical. Retries and research loops produce byte-identical
requests at rates human users never do. That’s rent nobody should pay twice.

3/ Exact-match caching on purpose — not semantic. “Almost the same prompt”
is not the same prompt. Near-miss answers turn savings into refunds.

4/ Compliant fetch is the other half: robots at fetch time, PII redacted,
SSRF blocked. Safe context for the model.

5/ HIT is a billable pipe event (metered, idempotent). The cache is
billing-grade, not best-effort. Control plane for teams:
withohm.dev/docs/enterprise-chaos

6/ MCP for @cursor_ai / Claude: pip install withohm-mcp
https://www.withohm.dev/i — works today without marketplace.

7/ $0 to connect. Share a public receipt → $35 bounty: withohm.dev/bounty
Repo: https://github.com/iwasinnam2/ohm
```

---

## 4. cursor.directory (primary — support deferred marketplace here)

Submit / update using the **chaos governor** packet in
[CURSOR_DIRECTORY.md](../listings/CURSOR_DIRECTORY.md) — not the old
Cursor-MCP trojan one-liner. Packet includes `/demo` + enterprise-chaos docs.

Checklist:

- [ ] Title/one-liner lead with control plane / chaos governor (Cursor optional)
- [ ] Links: site, `/demo`, `/docs/enterprise-chaos`, `/workbench`, `/org`, `/i`, GitHub
- [ ] Publisher note cites ticket T-E60068 → directory
- [ ] Record submit date in partner hit list notes

---

## 5. Steal-kit PRs (1–2 this sprint)

From [STEAL_KIT.md](STEAL_KIT.md):

1. `punkpeye/awesome-mcp-servers` — add withOhm row
2. Any second list/directory that accepts MCP entries

---

## Done when

- [ ] Forum §1 posted + thread URL logged
- [ ] r/cursor §2 posted
- [ ] X §3 posted
- [ ] cursor.directory submitted (chaos packet)
- [ ] ≥1 steal-kit PR opened
- [ ] Show HN fired per runbook (separate day, 2h live)
