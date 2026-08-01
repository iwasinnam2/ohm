# Show HN runbook — one shot, 2h live

Do not resubmit for ~6 months. Fire only when you can reply live for **≥2 hours**.

Copy source: [LAUNCH_POSTS.md](LAUNCH_POSTS.md) §1. Siege answers: [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md).

---

## When

- **Tue–Thu, 13:00–15:00 UK** (8–10am ET)
- Clear calendar for T+0 → T+2h

---

## Pre-flight (day before)

- [ ] Repo README: what it does + install in first screen — https://github.com/iwasinnam2/ohm
- [ ] Production smoke:

```powershell
.\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey $env:OHM_API_KEY
```

- [ ] Live surfaces: https://www.withohm.dev/i · /design-partners · /docs/cursor
- [ ] Health: `GET https://api.withohm.dev/health` and `/ready`
- [ ] First comment pasted in notepad (below) — post within **60 seconds** of submit
- [ ] [SIEGE_DEFENSE.md](SIEGE_DEFENSE.md) open (exact-match, charging for hits, Rust full-proxy, semantic cache)
- [ ] Optional: screenshot/GIF of identical request → cache hit / savings
- [ ] Gap surfaces ideally already live ([GAP_SURFACES.md](GAP_SURFACES.md)) so repo/traffic isn’t cold

---

## Submit fields

| Field | Value |
|-------|--------|
| **URL** | `https://github.com/iwasinnam2/ohm` (repo, not marketing site) |
| **Title** | `Show HN: withOhm – replay cache and compliant web fetch for LLM agents` |

Alternates (only if primary feels wrong that day):

```text
Show HN: withOhm – a Rust gateway that replays identical LLM calls from Redis
Show HN: withOhm – metered pipe for agents: cache replay, robots-aware fetch
```

---

## First comment (paste immediately)

```text
I built this after watching coding agents re-pay full token price for calls
they had already made (repeat prefill tax), and re-scrape pages with no
regard for robots.txt or what PII came back.

withOhm is an OpenAI-compatible pipe you point an agent at. Two things happen
in the pipe: (1) exact-replay caching — identical requests are served from
Redis instead of the provider, so a hit costs ~$2/M tokens instead of the
provider's full input+output price; (2) a compliance pipeline for web fetch —
robots.txt respected, PII redacted, SSRF-safe. MCP: pip install withohm-mcp.

Savings are a dual ledger on /v1/savings: estimated provider $ avoided
(blended list rate × hit tokens) vs Ohm pipe rent, plus roi_ratio — always
labeled estimate_only. Cache hits are billable events on purpose: withOhm
only makes money when it's saving you more. Exact-match only — semantic
cache turns savings into refunds. BYOK — your provider key rides in a header.

Repo is MIT. Scrutiny welcome on cache-key canonicalization and robots/PII.
Gem position: docs/GEM_POSITION.md
```

---

## During T+0 → T+2h

1. Reply to every substantive comment; concede real hits plainly.
2. Use siege copy for known attacks; do not argue tone.
3. Soft CTA **only when asked**: `$0` connect, `pip install withohm-mcp`, https://www.withohm.dev/i · design-partners.
4. **Pause** cold partner spray ([PARTNER_HIT_LIST.md](PARTNER_HIT_LIST.md)) until the window ends.
5. Log interesting HN handles into [partner_hit_list.csv](partner_hit_list.csv) as warm leads.

---

## Success criteria

- Sustained technical thread and/or front page
- Same-day spike in `/i` and key issuance
- At least one design-partner or Intermediate seat from HN traffic

---

## After

- [ ] Issue keys same-day for anyone who asks → [PARTNER_ONBOARD.md](PARTNER_ONBOARD.md)
- [ ] Resume 5/day outreach next morning
- [ ] Do **not** resubmit Show HN for six months
