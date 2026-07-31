# Launch posts — fire-ready copy

Register: builder sharing an interesting system. Factual, specific, a little
understated. No urgency, no "please try", no exclamation marks. We describe
what the thing does; the reader decides.

Venue research (Jul 2026): Show HN's top-performing category is open-source
tools with a GitHub link; titles 60–80 chars, sentence case, zero adjectives;
"I built" outperforms "We built". Reddit: disclose affiliation everywhere,
never cross-post identical text, and match each sub's format — r/mcp wants
launched projects with disclosure, r/LLMDevs wants architecture, r/SideProject
welcomes product drops, r/AI_Agents wants the problem discussed with the link
in comments.

---

## 1. Hacker News — Show HN

**When:** Tuesday–Thursday, 13:00–15:00 UK (8–10am ET). Hard rule: only post
when you can reply to comments for the following two hours. Front-page fate is
decided in the first 30–60 minutes; an unattended launch is a wasted launch.
Do not resubmit for six months, so spend this one deliberately.

**URL field:** https://github.com/iwasinnam2/ohm (repo, not the site — repos
outrank demos on HN; the site is one click from the README).

**Title (primary, 74 chars):**

```text
Show HN: withOhm – replay cache and compliant web fetch for LLM agents
```

**Alternates:**

```text
Show HN: withOhm – a Rust gateway that replays identical LLM calls from Redis
Show HN: withOhm – metered pipe for agents: cache replay, robots-aware fetch
```

**First comment (post within 60 seconds of submitting):**

```text
I built this after watching coding agents re-pay full token price for calls
they had already made, and re-scrape pages with no regard for robots.txt or
what PII came back.

withOhm is an OpenAI-compatible pipe you point an agent at. Two things happen
in the pipe: (1) exact-replay caching — identical requests are served from
Redis instead of the provider, streamed or not, so a hit costs ~$2/M tokens
instead of the provider's full input+output price; (2) a compliance pipeline
for web fetch — robots.txt respected at fetch time, PII redacted before the
content reaches the model, SSRF-safe with connect-time IP pinning. There's an
MCP server (pip install withohm-mcp) so Cursor/Claude agents get it as tools.

The architecture choice I'd defend: the edge is a small Rust proxy that
answers cache hits without touching the Python control plane, and hits are
metered as billable events at the edge. Caching is exact-match on a
canonicalized request — I deliberately did not do semantic caching, because
serving an almost-right answer from cache is worse than paying for the call.
Streamed responses replay too: the pipe assembles the stream on the way
through, and an identical request later gets the same completion back as SSE.

BYOK — your provider key rides in a header, or bring none and just use fetch.

Repo is MIT. I'd particularly like scrutiny on the cache-key canonicalization
and the robots/PII pipeline — if there's a hole in either, I want to know
before customers find it.
```

---

## 2. Reddit

Disclose ("I built this") in every post. Different text per sub — the copies
below share facts, not sentences. Space the posts across 2–3 days rather than
carpet-bombing in one hour.

### r/mcp — showcase (highest fit, post first)

**Title:**

```text
withOhm: MCP server for compliant web fetch + prompt cache replay (launched, MIT)
```

**Body:**

```text
Disclosure: my project.

withOhm gives agents two things through one MCP server:

- ohm_fetch_web — URL ingest with the compliance work done in the pipe:
  robots.txt respected at fetch time, PII redacted before content reaches the
  model, SSRF-guarded (connect-time IP pinning, no private ranges). The agent
  asks for a URL; what comes back is safe to put in context.
- ohm_chat — an OpenAI-compatible passthrough with exact-replay caching.
  Identical requests are answered from Redis instead of the provider. BYOK.

Also ships ohm_models / ohm_savings / ohm_usage / ohm_policy for
introspection, plus skills so the agent knows when to reach for each tool.

Install: pip install withohm-mcp — config is three env vars (docs in repo).
Server implementation is MIT: https://github.com/iwasinnam2/ohm

Design question I'd genuinely like this sub's take on: the fetch tool returns
a compliance verdict alongside content (what was redacted, what the robots
policy said). Is that verdict useful surface for your agents, or noise?
```

### r/cursor — workflow post

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
calls get replayed from Redis instead of re-billed by the provider.

Setup is pip install withohm-mcp plus an mcp.json entry — two minutes, config
on the site: https://www.withohm.dev/i

The skills are the part I'm most interested in feedback on: they teach the
agent when to use the pipe (e.g. "public URL context → ohm_fetch_web") so you
don't have to prompt for it. If you try it and the agent reaches for the
wrong tool, tell me — that's a skill-wording bug and cheap to fix.
```

### r/LLMDevs — architecture write-up (link at the end, not the top)

**Title:**

```text
Metering-first gateway design: Rust edge answers cache hits, Python owns billing truth
```

**Body:**

```text
Sharing the architecture of a system I just shipped (disclosure: mine), since
the interesting problems were all billing-adjacent rather than model-adjacent.

The system is a caching proxy for LLM calls. The design constraint that shaped
everything: a cache hit is a *billable event* (you charge for the replay), so
the cache cannot be a best-effort layer — it has to emit usage records with
the same reliability as the origin path.

What that forced:

- The edge is a small Rust proxy that serves exact-match hits straight from
  Redis and emits the meter event itself, idempotency-keyed, so a hit never
  depends on the Python control plane being up.
- Exact-match keys over canonicalized requests, not semantic similarity.
  Semantic caching reads great in a README and is a refund generator in
  production — "almost the same prompt" is not the same prompt.
- Streamed responses are assembled as they pass through and stored under the
  same key as the non-stream path — a later identical request gets the
  completion replayed as SSE. Partial streams are never cached; only a
  stream that finished cleanly becomes a cache entry.
- Stripe billing meters as the sink, with idempotency keys derived from the
  request hash, so retries can't double-bill.

Repo (MIT) if you want to read the edge code: https://github.com/iwasinnam2/ohm
Happy to go deep on any of it.
```

### r/AI_Agents — problem-first discussion (link in comments only)

**Title:**

```text
Agents re-buy the same tokens constantly — measured it, then built the boring fix
```

**Body:**

```text
Watching agent traces, a pattern kept showing up: research loops and retries
re-issue byte-identical model calls, and every one is billed at full price.
Same with web context — the same docs page fetched dozens of times across a
session, robots.txt never consulted, PII pasted straight into context.

The fix isn't clever: put a pipe in front of the provider, canonicalize and
hash each request, replay exact matches from Redis, and run every fetch
through a robots/PII/SSRF pipeline before it reaches the model.

What surprised me building it: exact-match hit rates in agent workloads are
much higher than intuition says, because agents are mechanical — retries,
self-consistency loops, and repeated tool calls produce identical requests in
a way human users never do.

Curious what hit rates others see, and whether anyone has made semantic
caching work in production without correctness incidents — I ruled it out
on purpose.

(I'll drop the repo in a comment for anyone who wants it — it's MIT.)
```

### r/SideProject — launch post (most promo-tolerant, lowest stakes, good warm-up)

**Title:**

```text
I built withOhm — agents pay rent on a pipe instead of re-buying the same tokens
```

**Body:**

```text
withOhm is a metered pipe for AI agents: identical LLM calls get
replayed from cache instead of re-billed by the provider, and web fetches go
through a compliance pipeline (robots.txt, PII redaction, SSRF guards) before
the content reaches the model.

Live at https://www.withohm.dev — $0 to connect, usage-priced, MIT repo.
Works with Cursor/Claude via MCP (pip install withohm-mcp), and streamed
responses replay from cache the same as regular ones.

Would love feedback on the pricing page specifically — is the meter pricing
legible to someone seeing it cold?
```

---

## 3. X thread

Post from the personal account; quote-tweetable single-claim tweets. Tag
@cursor_ai only in tweet 6, where it's factual rather than thirsty.

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

5/ Architecture: Rust edge answers cache hits straight from Redis and meters
them at the edge — a hit is a billable event, so the cache path is built to
billing-grade reliability, not best-effort.

6/ It's an MCP server, so @cursor_ai and Claude agents get it as native tools:
pip install withohm-mcp. Plugin is in marketplace review; works today
without it.

7/ $0 to connect, priced per use ($2/M cached tokens, $3/1k compliant
fetches). Repo: https://github.com/iwasinnam2/ohm — the cache-key and
compliance code is the part worth reading.
```

---

## 4. Firing order

| When | Action | Why |
|---|---|---|
| Tonight (any time) | r/SideProject + X thread | Promo-tolerant venues, async-safe, warms the repo with traffic before HN |
| Tomorrow | r/mcp, then r/cursor a few hours later | Highest-intent audiences; distinct copy avoids cross-post filters |
| Day 3 | r/LLMDevs + r/AI_Agents | Technical/discussion framing lands better once the repo shows activity |
| First day you can guard 2 hours (Tue–Thu, 13:00–15:00 UK) | Show HN | Front page is decided in the first hour; never fire this unattended |

Rules that protect the account: disclose everywhere; never post identical
text to two subs; answer every substantive comment (HN: within 15 minutes for
the first two hours); if a comment finds a real flaw, concede it plainly —
intellectual honesty is the currency on every one of these venues.

---

## 5. Universal template (one body, per-venue title + ask)

The spine below works on every venue; only the title and the closing ask
change. Swap the two `[...]` slots, post. Change at least the opening
sentence's word order between subs so filters see distinct text.

**Body:**

```text
Disclosure: my project.

The observation this is built on: agents are mechanical. Retries, research
loops, and repeated tool calls issue byte-identical LLM requests at rates
human users never do — and every single one is billed at full token price.
Web context is the same story told twice: the same docs page fetched dozens
of times a session, robots.txt never consulted, PII pasted straight into the
model's context. Agents are quietly re-buying work they already paid for, and
nobody is watching the pipe.

withOhm is that pipe, watched. Point an agent at one OpenAI-compatible
endpoint and everything flowing through it gets smarter:

- Cache replay — every request is canonicalized and hashed; when an
  identical one comes back, the answer is replayed straight from Redis
  instead of the provider, streamed or not, at ~$2/M tokens instead of full
  input+output price. Exact-match by design: "almost the same prompt" is not
  the same prompt, and near-miss answers are how a savings feature becomes a
  refunds feature. The replay path is billing-grade — a Rust edge answers
  hits and meters them as first-class events, so the cache is never
  best-effort.
- Compliant fetch — hand it a URL and what comes back is actually safe to
  put in context: robots.txt consulted at fetch time, PII redacted before
  the model ever sees the content, SSRF blocked at connect time with IP
  pinning. The compliance verdict rides along with the content, so the agent
  knows what was redacted and why.

Using it takes about two minutes: pip install withohm-mcp, add the MCP
config, and Cursor/Claude agents pick up the tools natively — ohm_chat for
the cached pipe, ohm_fetch_web for clean URL context, ohm_savings to watch
what the cache is earning you in real time. BYOK: your provider key rides in
a header, and cache hits never need one. Connecting costs $0; you pay for
what moves through the pipe.

Site: https://www.withohm.dev
Repo (MIT): https://github.com/iwasinnam2/ohm
Two-minute install: https://www.withohm.dev/i

Under the hood: Rust edge gateway, Redis, Python control plane. All of it is
in the repo — read the implementation rather than taking the README's word.

[ASK]
```

Thread-answer note (not for the post): if a commenter asks about regions,
answer honestly — served from us-east-1 today, expansion is demand-gated. If
asked about paraphrases: exact-match is deliberate; canonicalization strips
non-semantic noise (whitespace, line endings) but never guesses at meaning.

**Title slot per venue:**

| Venue | Title |
|---|---|
| r/mcp | withOhm: MCP server for compliant web fetch + prompt cache replay (launched, MIT) |
| r/cursor | Built a plugin that gives the Cursor agent compliant web fetch and replays repeated calls from cache |
| r/SideProject | withOhm — agents pay rent on a pipe instead of re-buying the same tokens (went live this week) |
| r/LLMDevs | Metering-first gateway: Rust edge answers cache hits, exact-match over semantic on purpose |
| r/AI_Agents | Agents re-buy the same tokens constantly — so I built the boring fix |
| Show HN | Show HN: withOhm – replay cache and compliant web fetch for LLM agents |

**Ask slot per venue:**

| Venue | Closing ask |
|---|---|
| r/mcp | The fetch tool returns a compliance verdict alongside the content (what was redacted, what robots.txt said). Useful surface for your agents, or noise? |
| r/cursor | The plugin ships skills that teach the agent when to reach for the pipe on its own. If it grabs the wrong tool, say so — that's a skill-wording bug and cheap to fix. |
| r/SideProject | Feedback valued most: is the pricing page legible to someone seeing it cold? https://www.withohm.dev/subscriptions |
| r/LLMDevs | Happy to go deep on the cache-key canonicalization or the idempotent metering — ask away. |
| r/AI_Agents | Has anyone made semantic caching work in production without correctness incidents? It was ruled out here on purpose, but I'd be interested in a counterexample. |
| Show HN | Scrutiny most wanted on the cache-key canonicalization and the robots/PII pipeline — if there's a hole in either, better to hear it here first. |

Venue-specific mechanics: r/AI_Agents — move the three links into a comment,
keep the body link-free. HN — repo URL in the URL field, the body becomes the
first comment (posted within 60 seconds, Disclosure line dropped).

---

## 6. Floodgate copy (final — verified 17/17 production pre-flight, 2026-07-31)

Four fully distinct posts, fired simultaneously. Answer every substantive
comment; concede real flaws plainly.

### r/mcp

**Title:** withOhm: MCP server for compliant web fetch + prompt cache replay (launched, MIT)

```text
Disclosure: my project. Launched this week and live now.

withOhm gives agents one pipe with two disciplines built into it:

ohm_fetch_web — URL ingest with the compliance work done in the pipe, not
left to the agent: robots.txt consulted at fetch time, PII redacted before
content ever reaches a model, SSRF blocked at connect time with IP pinning.
The tool returns a compliance verdict alongside the content — what was
redacted, what the robots policy said — so the agent can reason about what
it received, not just consume it.

ohm_chat — an OpenAI-compatible passthrough with exact-replay caching.
Requests are canonicalized and hashed; identical ones are answered from
Redis instead of the provider, streamed or not. A streamed response is
assembled as it passes through and replays later as SSE from the same cache
entry a JSON request would use. Hits are metered as first-class billable
events, which forced the cache to be billing-grade rather than best-effort.

Also ships ohm_models / ohm_savings / ohm_usage / ohm_policy for
introspection, plus skills so the agent knows when to reach for each tool
without prompting.

Install: pip install withohm-mcp (three env vars, docs in repo).
Repo (MIT): https://github.com/iwasinnam2/ohm
Site: https://www.withohm.dev — $0 to connect, priced per use.

The design question I'd genuinely value this sub's take on: is the
compliance verdict useful surface for your agents, or noise? It's the part
of the tool contract I've iterated on most and I'd rather shape it around
real agent architectures than my own guesses.
```

### r/cursor

**Title:** Built a plugin that gives the Cursor agent compliant web fetch and replays repeated calls from cache

```text
Disclosure: my project. The plugin is in marketplace review, but it works
today without the marketplace — pip install withohm-mcp plus an mcp.json
entry, about two minutes: https://www.withohm.dev/i

The itch it scratches: Cursor agents doing research re-fetch the same pages
over and over, raw fetches ignore robots.txt entirely, and whatever PII is
on the page goes straight into context. Meanwhile the same retries and
research loops re-issue byte-identical model calls, each one billed at full
price.

withOhm sits between the agent and the web/provider and fixes both in the
pipe. Fetches come back robots-respecting, PII-redacted, and SSRF-safe,
with a verdict attached saying what was cleaned and why. Identical chat
calls — streamed or not — replay from Redis instead of being re-billed.
There's an ohm_savings tool so you can watch what the cache is earning you
in real time, which turns out to be weirdly compelling to check.

The part I most want feedback on is the skills: they teach the agent when
to reach for the pipe on its own (public URL context → ohm_fetch_web), so
you never have to prompt for it. If your agent grabs the wrong tool, say so
— that's a skill-wording bug and cheap to fix.

Repo is MIT if you want to read what the pipe actually does:
https://github.com/iwasinnam2/ohm
```

### r/LLMDevs

**Title:** Metering-first gateway design: Rust edge answers cache hits, exact-match over semantic on purpose

```text
Sharing the architecture of a system I shipped this week (disclosure: mine),
because the interesting problems were all billing-adjacent rather than
model-adjacent.

The system is a caching proxy for LLM calls. One constraint shaped every
decision: a cache hit is a billable event — you charge for the replay — so
the cache cannot be a best-effort layer. It has to emit usage records with
the same reliability as the origin path.

What that constraint forced:

- A small Rust edge serves exact-match hits straight from Redis and emits
  the meter event itself, idempotency-keyed, so a hit never depends on the
  Python control plane being up.
- Exact-match keys over canonicalized requests, not semantic similarity.
  Semantic caching reads great in a README and is a refund generator in
  production — "almost the same prompt" is not the same prompt. The
  canonicalization strips genuine transport noise (CRLF vs LF, outer
  whitespace) and never touches interior whitespace, because code blocks
  are semantics.
- The cache key is computed independently in Python and Rust, so the two
  implementations are pinned to the same digest by parity tests on both
  sides — if either drifts, the tests fail before edge hits silently vanish.
- Streamed responses are assembled as they pass through and stored under
  the same key as the JSON path; an identical request later replays as
  synthesized SSE. Only streams that finished cleanly (finish_reason seen)
  become cache entries — partial streams are never cached.
- Stripe billing meters are the sink, idempotency keys derived from the
  request hash, so retries can't double-bill.

Repo (MIT) if you want to read the edge code and the parity tests:
https://github.com/iwasinnam2/ohm

Happy to go as deep as anyone wants on the cache-key canonicalization or
the idempotent metering — those two are where the correctness lives.
```

### r/AI_Agents (links go in a first comment, body stays link-free)

**Title:** Agents re-buy the same tokens constantly — so I built the boring fix

```text
Watching agent traces, a pattern keeps showing up: research loops, retries,
and self-consistency passes re-issue byte-identical model calls, and every
single one is billed at full token price. Web context is the same story —
the same docs page fetched dozens of times a session, robots.txt never
consulted, PII pasted straight into context.

Agents are mechanical in a way human users never are, and that mechanical
repetition is exactly what makes the boring fix work: put a pipe in front
of the provider, canonicalize and hash every request, replay exact matches
from Redis (streamed responses included — the pipe assembles them on the
way through and replays them as SSE), and run every fetch through a
robots/PII/SSRF pipeline before the content reaches the model.

The deliberately unfashionable choice was exact-match over semantic
caching. "Almost the same prompt" is not the same prompt, and serving a
near-miss from cache is how a savings feature becomes a refunds feature.
Canonicalization strips transport noise — line endings, outer whitespace —
and refuses to guess at meaning.

Question for the sub: has anyone made semantic caching work in production
without correctness incidents? I ruled it out on purpose and I'd genuinely
like to see a counterexample that survives real traffic.

(Repo and site in the first comment — it's MIT.)
```

**r/AI_Agents first comment:**

```text
Repo (MIT): https://github.com/iwasinnam2/ohm
Live: https://www.withohm.dev — $0 to connect, priced per use
MCP install for Cursor/Claude agents: pip install withohm-mcp
(https://www.withohm.dev/i)
```
