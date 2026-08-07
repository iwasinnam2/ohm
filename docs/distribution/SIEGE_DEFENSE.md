# Siege defense — prepared responses for the launch threads

Every accusation the four launch posts can draw, ranked by likelihood times
damage, each with a canonical response. The doctrine is constant: concede
what is true immediately, correct what is false precisely, never get
defensive, never argue tone. A concession delivered fast and plainly earns
more than any rebuttal.

Facts these responses rest on (verified against code, 2026-07-31):

- Cache key includes `temperature`, `max_tokens`, and `cache_control` in
  extras (`src/at_utility/cache.py`, call site in `main.py`).
- Cached completions are TTL-bound: `at_cache_ttl_seconds`, default 3600s.
- BYOK is a per-request header (`X-Ohm-Upstream-Key`), never persisted;
  cache hits require no upstream key.
- Training on cache contents is hard-denied in code
  (`assert_cache_training_denied`).
- The Rust edge supports Redis TLS (`rediss://`); production edge HITs go
  live when cluster secrets point at ElastiCache (see `docs/OPERATIONS.md`
  "Edge cache tier"). Until then the edge may full-proxy — correctness OK.
- `/v1/savings` is a **dual ledger**: provider-list estimate
  (`estimated_provider_avoided_usd`, default $15/M × hit tokens) vs
  `pipe_rent_usd`, plus `roi_ratio`. Always `estimate_only: true` — not a
  guaranteed savings promise. See `docs/GEM_POSITION.md`.

---

## Tier 1 — will appear, answer within minutes

### "Exact-match caching never hits in real traffic"

> Fair instinct for human traffic — humans never type the same thing twice.
> Agents do, constantly: retries after tool errors, self-consistency loops,
> CI pipelines re-running the same prompt suite, the same system prompt +
> file content pair resubmitted across a session. The traffic is mechanical,
> which is exactly why exact-match works here and nowhere else. You don't
> have to take my word for it: connecting is $0 and /v1/savings shows your
> own tenant's hit ratio and avoided spend. If your workload never repeats,
> the pipe costs you nothing and you've lost two minutes.

### "You charge for cache hits? You're billing me for not doing work"

> The replay is the work — the hit is served at ~$2/M tokens against the
> provider's full input+output price for the same call, and every response
> carries X-AT-Billed-USD so there's no mystery about what a request cost.
> The alternative pricing model is a subscription you pay whether the cache
> earns you anything or not. Metering the hit keeps the incentive honest:
> withOhm only makes money when it's saving you more. /v1/savings shows both
> sides: estimated provider $ avoided (blended list rate) and Ohm pipe rent,
> plus roi_ratio — all labeled estimate_only.

### "Cached replay breaks sampling — temperature > 0 should give different answers"

> True, and it's a real trade, so it's disclosed rather than hidden:
> temperature and max_tokens are part of the cache key, every hit is marked
> X-AT-Cache: HIT with purpose "identical-request-replay", and
> cache_control: "no_store" opts any request out. The bet is that when an
> agent re-issues a byte-identical request it's a retry or a loop, not a
> genuine request for fresh sampling diversity — and when it is the latter,
> you say no_store. If you want per-tenant sampling-aware bypass defaults,
> that's a reasonable feature request and cheap to add.

### "Why not LiteLLM / Helicone / Portkey / provider-native prompt caching?"

> Different jobs. Provider prompt caching discounts repeated *input prefix*
> tokens on a continuation — it never replays a full response, doesn't work
> cross-provider, and does nothing for web fetch. Gateway proxies like
> LiteLLM are routing layers; their caching is best-effort and unbilled,
> which is fine until you want to build a product on top of the cache.
> withOhm's cache is billing-grade (digest-scoped meter event identifiers, parity-
> pinned keys) and it ships the compliance fetch pipe and MCP tools in the
> same pipe. If you just need routing, use LiteLLM — genuinely.

---

## Tier 2 — likely, answer from posture

### "You're a MITM for my provider keys and prompts"

> The provider key rides per-request in the X-Ohm-Upstream-Key header and is
> never stored — cache hits don't need it at all. Cached completions live in
> tenant-namespaced Redis keys with a 1-hour default TTL, and training on
> cache contents is denied in code, not just in the terms (the assertion is
> in the repo, grep assert_cache_training_denied). If that trust bar still
> isn't met — reasonable for some workloads — the repo is MIT and
> self-hosting is supported.

### "'Compliant' is a legal claim you can't make"

> Fair pressure on the word. The pipe applies compliance *controls* —
> robots.txt consulted at fetch time, PII redaction before model contact,
> SSRF blocked at connect — and returns a verdict saying what it did.
> That's engineering diligence surfaced for audit, not a certification, and
> nobody should read it as a lawyer. If the verdict surface would be more
> useful with different framing, that's exactly the feedback I'm here for.

### "PII regex redaction is unreliable"

> True of every redactor ever shipped, including this one. The honest
> version of the claim: high-signal patterns (emails, phone numbers, card
> numbers) are caught, novel formats will get through, and the verdict tells
> you what was caught so the failure mode is visible rather than silent.
> Counterexamples gratefully taken — a reproducible miss is a test case
> within the day.

### "Single region / no SLA / solo project — what happens when you disappear?"

> Served from us-east-1 today; expansion is revenue-gated and the trigger is
> written down in the ops docs rather than promised vaguely. No SLA is
> claimed anywhere. The disappearance hedge is structural, not personal:
> MIT license, self-hostable, and the proxy fails open — if withOhm dies
> mid-request your traffic degrades to what it was before withOhm existed.

### "The Rust edge doesn't even serve hits — your own ops doc says it's degraded"

> Correct when production secrets still point the edge Redis URL at a null
> sink (or leave write/TLS miswired): the edge full-proxies and Python
> serves hits — correctness and billing stay intact. The Rust RESP client
> already speaks TLS (`rediss://` / `AT_RS_REDIS_TLS`); turning edge HITs
> on is an ops secrets flip, not a missing client. Documenting a degraded
> tier instead of quietly routing around it is the posture the whole
> system takes — the billing numbers have to be auditable, so the
> architecture claims have to be too. See `docs/OPERATIONS.md` "Edge cache
> tier".

---

## Tier 3 — possible, low damage

### "This repo smells AI-generated / vibe-coded"

> The code was written with agent assistance, like most code shipped this
> year. Judge it the way you'd judge any repo: the test suite, the
> cross-language digest parity pins, INSPECTION.md mapping every claim to
> the test that enforces it, and a 17/17 production pre-flight before
> launch. If you find a claim the tests don't back, that's a real hit —
> take the shot.

### "Metered billing on cache hits — what stops double-billing on retries?"

> Stripe meter `identifier`s are digest-scoped for HIT/MISS (`cache_hit:{sha}:plane`
> / `cache_miss:{sha}:plane`). A retried sync of the **same** logical event lands
> on the same key and Stripe deduplicates within its window. A second successful
> HIT on the same digest from the **same plane** shares that key (idempotent
> meter sync), which is the intended retry-safe behaviour — not "never bill two
> distinct HIT crossings." The metering code is in the repo.

### "SSE replay can't be faithful to the original stream"

> It replays the completion, not the original chunk timing — assembled on
> the way through, stored only if the stream finished cleanly
> (finish_reason seen), synthesized back as SSE on a hit. Truncated streams
> are never cached; there's a test asserting exactly that.

### "Robots.txt isn't law / this launders scraping as compliance"

> Robots is a voluntary protocol, and honoring it voluntarily is the point —
> the pipe defaults to declining what the site declined, which is more than
> raw fetch tools do. Purpose gating (public_web_retrieval and friends,
> blocked purposes rejected) rides on top. It doesn't make scraping legal
> or illegal; it makes the agent's behavior legible.

---

## Do-not-claim list (hold the line even under pressure)

- No encryption-at-rest claims for Redis until verified against the actual
  ElastiCache configuration.
- No legal compliance guarantees — GDPR, CCPA, copyright. Controls and
  verdicts, never certifications. Point at `/docs/copyright` for excerpt-cap
  posture (`controls_not_certification`).
- No uptime or SLA numbers.
- No "edge serves hits in production" — designed to, currently full-proxies,
  say it in that order.
- No hit-rate promises — point at /v1/savings and let tenants measure their
  own workloads.
