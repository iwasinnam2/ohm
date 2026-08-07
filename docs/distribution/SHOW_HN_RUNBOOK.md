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

- [ ] Live surfaces: https://www.withohm.dev/demo · /i · /design-partners · /docs/cursor
- [ ] Incognito waste check works (MISS → HIT) with public proof key if configured
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
If you’ve burned through a coding-agent quota mid-month on loops and retries,
this is the pattern: identical calls get re-billed every time.

Sixty-second proof: https://www.withohm.dev/demo
Same prompt twice → MISS then HIT. The second call does not re-buy the model.

withOhm is an OpenAI-compatible pipe: exact-replay caching (streamed or not),
compliant web fetch (robots / PII / SSRF), BYOK. MCP: pip install withohm-mcp
→ https://www.withohm.dev/i

Savings are a dual ledger on /v1/savings (provider avoided vs pipe rent) —
always estimate_only. Exact-match only; semantic cache turns savings into
refunds. Cache hits are billable events on purpose.

Repo MIT. Scrutiny welcome on cache-key canonicalization and robots/PII.
Siege FAQ lives in docs/distribution/SIEGE_DEFENSE.md
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
