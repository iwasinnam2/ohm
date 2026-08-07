# Care Audit — Methodological Appendix

**Status:** Phases 0–2 executed (2026-08-07); Phases 3–4 pending  
**Themes:** (1) care, (2) attention to detail  
**Issued:** 2026-08-07  
**Scope:** full monorepo — runtime, site, MCP, pricing, catalogues, docs, GTM ops  

This is not a feature roadmap. It is a **truth-maintenance program**: every public
claim, every meter, every CTA, every catalogue row must stay aligned with what
the code actually does under load — including the degraded paths we ship on
purpose.

---

## 0. What this product is (shared model)

withOhm is a **metered tollbooth** between agent hosts and LLM providers:

```
Host (Cursor / Claude / SDK)
  → api.withohm.dev:443  (Rust edge :8081)
      → Redis GET  → HIT → POST /internal/edge-hit (meter) → replay
      → MISS       → Python control plane :8080
                        → auth / tenancy / soft caps
                        → optional ingest :8090 (robots / SSRF / PII)
                        → upstream BYOK (X-Ohm-Upstream-Key)
                        → Redis SET (unless no_store)
                        → Stripe meter events
  ↔ www.withohm.dev (Amplify) — proof, seat, docs, bounty, receipts
```

**What we sell:** pipe rent on exact-match replay + compliant public-web context —
not managed tokens, not semantic cache, not RAG.

**Commercial spine:**

| Layer | Name in UI | Name in API/Stripe | Price |
|-------|------------|--------------------|-------|
| Seat | Intermediate | `payg` / `STRIPE_PRICE_PAYG` | $0 / mo |
| Meters | hit / miss / fetch | `ohm_cache_hit` / `_miss` / `_web_fetch` | rate card v2 |
| Commit | c29 / c99 / c499 | same ids | $29→$35 … $499→$700 included |
| Enterprise | contact | negotiated | from $2500/mo (card) |

**Canonical money truth:** `pricing/rate_card.v2.json` (mirrored to
`site/src/lib/rate_card.v2.json`; Python defaults asserted by
`tests/test_rate_card.py`).

**Proof spine (indie):** homepage → `/demo` waste check (MISS→HIT) → `/r/…`
receipt → `/bounty` ($100 credit, social post required) → `/i` MCP meme →
`/billing/intermediate`.

**Thesis spine (enterprise / directories):** chaos governor — locality, cache
trees, spend caps, SCIM/org — not Pro+ quota burn.

**Hard constraints already decided:**

- Show HN is **blocked** (HN account banned). Do not attempt.
- Do not re-flood identical Reddit launch copy.
- `model: mock` proves cache + meters offline; real models need BYOK.
- Docker Compose is documented; cloud agents run services **natively**.

If you do not hold this model, every “care” fix below will look like random
polish. Care here means: **the product’s mouth matches its hands.**

---

## 1. Method — how this audit was run

### 1.1 Axes (two themes)

| Theme | Definition used here | Failure mode |
|-------|----------------------|--------------|
| **Care** | We refuse silent lies — degraded modes are named, billed paths are auditable, GTM does not promise blocked channels | Siege reply that invents “TLS is next” when TLS exists; bounty CTA on a public proof key; Show HN still listed as fireable |
| **Attention to detail** | Single source of truth; catalogues count what ships; vernacular maps; CI catches drift | “seven MCP tools” while eight ship; `/pricing` hardcodes rates; partner CSV all `[fill]` labeled “done” |

### 1.2 Evidence classes

1. **Runtime** — Python `at_utility`, Rust `gateway-rs`, ingest worker, Redis roles  
2. **Public surface** — site routes, API routes, MCP tools, Cursor skills/plugin  
3. **Money** — rate card, Stripe meters, Intermediate/payg, commit tiers, soft caps  
4. **Catalogues** — docs trees, listings, partner CSV, steal-kit, INSPECTION claims  
5. **Ops / GTM** — waste check, siege defense, readiness, Amplify env glue  

### 1.3 Severity

| Sev | Meaning |
|-----|---------|
| **P0** | Correctness / privacy / billing claim broken in a path customers can hit |
| **P1** | Public truth mismatch (docs/UI/GTM contradict code or each other) |
| **P2** | Silent degradation, orphan inventory, vernacular fracture, process theater |
| **P3** | Cosmetic / deferred rename / historical residue |

### 1.4 Non-goals of this pass

- New features, new meters, new regions  
- Full `at_*` → `ohm_*` rename  
- Re-opening Show HN  
- Changing rate card economics (only SoT wiring)

---

## 2. Full surface catalogue

### 2.1 Runtime planes

| Plane | Dir / binary | Port | Job |
|-------|--------------|------|-----|
| Rust edge | `gateway-rs/` → `at-gateway-rs` | 8081 | Public `/v1`; Redis GET HIT; proxy MISS |
| Python control | `src/at_utility/` | 8080 | Auth, SET, providers, Stripe, org, receipts |
| Ingest | `workers/ingest_worker.py` | 8090 | Compliant public URL fetch |
| Redis | primary + optional replica | 6379 | Cache / tenants / meters / RL |
| Site | `site/` Next.js | 3000 | Marketing, docs, billing, demo, bounty |
| MCP HTTP | `ohm-mcp` | 8091 | Streamable HTTP `/mcp` (plus stdio) |

Auth: Bearer `sk-at-*` (legacy prefix; brand is withOhm). Bootstrap
`sk-at-dev` → `tenant_bootstrap_{last8}` on both planes so cache keys align.
Edge auth enum: `Allowed` | `Denied` | `Unverified` (Redis outage → full-proxy).

Cache keys: `at:{tenant}:cache:v2:{digest}` (main);
`at:{tenant}:tree:{id}:cache:v3:{digest}` (named trees). Digest includes
`model`, `messages`, `temperature`, `max_tokens`, `cache_control`, web fields.

### 2.2 Public site routes (care-relevant)

| Route | Role in funnel |
|-------|----------------|
| `/` | Hero; primary **waste check** CTA |
| `/demo` | Prove MISS→HIT (public key or paste) |
| `/r/[token]` | Public savings receipt |
| `/bounty` | $100 meter credit (seat key + social URL) |
| `/i` | MCP install meme |
| `/billing/intermediate` | $0 seat checkout |
| `/subscriptions` | Plans from rate card imports |
| `/pricing` | **Hardcoded** tables (drift risk) |
| `/connections`, `/keys`, `/workbench` | Attach / Agent Shell |
| `/docs/*` | MDX from `site/content/docs/` |
| `/product/*`, `/use-cases/*` | Narrative |
| `/status` | Retired (`notFound`); truth in `/docs/status` |

### 2.3 API catalogue (customer-facing)

- Chat: `POST /v1/chat/completions`, `GET /v1/models`, `GET /v1/providers`  
- Money: `/v1/usage`, `/v1/savings`, `/v1/savings/receipt`, ledger  
- Public honesty: `/v1/public/{honesty,stats,receipts/*}`  
- Compliance: `/v1/compliance/policy`  
- Billing: `/v1/billing/{checkout,claim-key,webhook}` (topup 410)  
- Internal: `POST /internal/edge-hit`  
- Health: `/health`, `/ready`

### 2.4 MCP + skills catalogue

**Code ships 8 tools** (`src/ohm_mcp/__init__.py` / `packages/ohm-mcp/`):

1. `ohm_chat`  
2. `ohm_fetch_web`  
3. `ohm_usage`  
4. `ohm_models`  
5. `ohm_savings`  
6. `ohm_receipt`  
7. `ohm_providers`  
8. `ohm_policy`  

**Agent Shell catalog** lists all 8 (`site/src/lib/ohmShellCatalog.ts`).  
**Docs/UI still say seven** and often omit `ohm_receipt` from the inventory table.  
**Cursor skills** ship 7 slash skills — no `ohm-receipt` skill mirror.

### 2.5 Docs / ops catalogue (trees)

| Tree | Count (approx) | Audience |
|------|----------------|----------|
| `docs/` | ~61 md | Operators, GTM, legal source, architecture |
| `docs/distribution/` | waste check, siege, partners, sprint, steal-kit | Launch ops |
| `docs/listings/` | marketplace / directory packets | Distribution |
| `docs/automation/` | daily upkeep, Slack slash | Ops automation |
| `site/content/docs/` | ~25 | Public docs MDX |
| `site/content/product|use-cases` | ~12 | Narrative |
| `INSPECTION.md` (root) | claims → tests | Honesty map |
| `AGENTS.md` | cloud agent runbook | Agents |
| `.cursor/skills`, `.cursor-plugin/` | Ohm attach | Cursor |

---

## 3. Vernacular map (fracture inventory)

| Term | Means | Fracture |
|------|-------|----------|
| **withOhm / Ohm / Ω** | Public brand | Fine; README still “Ohm (withOhm)” |
| **at_utility / sk-at- / X-AT-*** | Deferred rename internals | First-read tax on every new engineer |
| **Intermediate** | $0 seat UI name | |
| **payg** | Same plan in API/Stripe | Must always say “Intermediate ↔ payg” once |
| **waste check** | `/demo` indie proof | Competes with header “$0 seat” as primary CTA |
| **Pro+** | Cursor competitor pain | Not an Ohm SKU — easy misread |
| **chaos governor** | Enterprise thesis | Strong in listings; weak on consumer home |
| **tollbooth / pipe / pipe rent** | Metaphors | Tollbooth rare; pipe dominant — pick one lead metaphor per surface |
| **fail-closed** | robots, Slack allowlist, definitive unknown keys | Mis-cited for edge Redis outage (actually **Unverified** fail-open proxy) |
| **Unverified** | Edge auth when Redis lookup fails | Correctness OK; marketing “fail-closed edge” is the lie |

---

## 4. Findings (evidence-ranked)

### P0 — Correctness

#### F1. Rust edge SET after MISS ignores `no_store` / BYPASS — **fixed (Phase 2)**

Edge skips SET when request `cache_control=no_store` or response
`x-at-cache: BYPASS`. `resolve_tenant` no longer invents `tenant_{suffix}`.
Unit: `should_skip_edge_set`. Python path remains `test_no_store_skips_cache_write`.

### P1 — Public truth

#### F2. MCP inventory: “seven” vs eight — **fixed (Phase 0/1)**

Docs/UI/package README now say **eight** and list `ohm_receipt`. Asserted by
`tests/test_mcp_catalogue.py`. `/ohm-receipt` skill mirrored.

#### F3. `/pricing` hardcodes rate card — **fixed (Phase 1)**

`site/src/app/pricing/page.tsx` imports `PAYG_RATES` / `COMMIT_TIERS`. Site JSON
mirror asserted equal to `pricing/rate_card.v2.json`.

#### F4. Siege FAQ still says “plain TCP / TLS is next” — **fixed (Phase 0)**

SIEGE_DEFENSE + LAUNCH_POSTS now match OPERATIONS (secrets / null sink; TLS
client already in-repo).

#### F5. Fail-closed vs Unverified wording — **fixed (Phase 0)**

READINESS / MARKETPLACE_AUDIT quote Unverified full-proxy accurately.

#### F6. Bounty CTA on public-key proofs — **fixed (Phase 0)**

Public-key receipts primary-CTA to `/signup`; Claim bounty only on seat keys.

#### F7. Show HN residue in fire-day copy — **fixed (Phase 0)**

SPRINT_GTM title + PARTNER_HIT_LIST fire-day language mark Show HN **BLOCKED**.

### P2 — Degradation / process theater

#### F8. MemoryStore silent fallback — **hardened (Phase 2)**

`/ready` reports `redis.backend`; MemoryStore in non-dev regions → 503.
Boot still falls back with a warning (local/dev/test stay ready).

#### F9. Soft-cap honesty on edge HIT — **documented (Phase 2)**

OPERATIONS: soft-cap warning headers are MISS-only (hard 402 still via gate).

#### F10. REDIS_MESH status table vs torn-down banner — **fixed (Phase 0)**

Live vs archive tables separated.

#### F11. Partner CSV all `[fill]` — **open (Phase 3)**

`partner_hit_list.csv` — 20 placeholder rows. Docs treat CSV as a pipeline
artifact; it is still a template.

#### F12. CTA / nav disunity — **named (Phase 0)**

BRAND + WASTE_CHECK CTA doctrine: hero=belief, header=conversion, Log in=return.

#### F13. Skills gap for `ohm_receipt` — **fixed (Phase 1)**

`ohm-receipt` skill in `.cursor/skills`, plugin, `skills/`, steal-kit template.

#### F14. Stripe `stripe_synced: false` forever without customer

Local accrual continues; flag is last-ok bit, not “all events synced”. Fine
for local smoke; easy to misread in support.

#### F16. No classic login/sign-up surface (fixed 2026-08-07)

Marketing had only “Start — $0 seat” → Intermediate checkout and key paste on
`/keys`. Added `/login` (restore `sk-at-…`) and `/signup` (Intermediate form)
with header Log in + Start CTA → `/signup`. Still no email/password — honesty
copy on the gate.

### P3 — Deferred

- Full brand rename (`at_*` → `ohm_*`, `sk-at-` → `sk-ohm-`)  
- Stream HIT at edge (explicitly deferred; Python-only replay)  
- Multi-region mesh rebuild  

---

## 5. Sources of truth — intended map

| Domain | Single source of truth | Consumers that must import, not copy |
|--------|------------------------|--------------------------------------|
| Money | `pricing/rate_card.v2.json` | Python config (tested), `site/src/lib/rate_card.v2.json`, `/pricing`, `/subscriptions`, docs pricing MDX |
| MCP tools | `@mcp.tool` list in `ohm_mcp/__init__.py` | Package README, INTEGRATIONS, commands.md, ConnectionsClient, CURSOR.md, skills |
| Hosts / brand | `docs/BRAND.md` | Site, listings, emails |
| Edge degraded mode | `docs/OPERATIONS.md` “Edge cache tier” | SIEGE_DEFENSE, LAUNCH_POSTS, STATUS |
| Fail postures | Code enums + OPERATIONS | READINESS, MARKETPLACE_AUDIT (must quote Unverified accurately) |
| Indie funnel | `docs/distribution/WASTE_CHECK.md` | Home, demo, bounty, GAP_SURFACES |
| Enterprise thesis | `docs/ENTERPRISE_CHAOS.md` + listings | Directory, marketplace, `/docs/enterprise-chaos` |
| Claims → tests | `INSPECTION.md` | Any new public claim |

**Rule:** if a number or count appears in two places, one is wrong until proven
imported.

---

## 6. Remediation program (phases)

### Phase 0 — Truth bleed-stop (docs/UI only, no runtime risk)

Stop the product from lying in public threads and funnels.

1. Fix SIEGE_DEFENSE + LAUNCH_POSTS TLS wording → match OPERATIONS (secrets /
   null sink, not “TLS next”).  
2. Strike / rewrite Show HN fire-day language to **BLOCKED** everywhere
   remaining.  
3. MCP: change “seven” → **eight**; add `ohm_receipt` to every inventory table;
   sync package README.  
4. Bounty: hide primary Claim CTA when `usingPublicKey`; seat CTA primary.  
5. READINESS / MARKETPLACE_AUDIT: replace “Rust fail-closed on Redis auth
   error” with accurate Unverified / full-proxy language.  
6. REDIS_MESH: label historical table **archive** or align with STATUS.  
7. Nav: either add Demo to primary resources, or document dual CTA doctrine in
   BRAND / WASTE_CHECK so the split is intentional.

**Exit:** a hostile reader with SIEGE open cannot catch us in a TLS or tool-count
lie; public demo cannot claim bounty on the shared key.

### Phase 1 — Single source of truth wiring

1. `/pricing` page imports `PAYG_RATES` / `COMMIT_TIERS` (same as subscriptions).  
2. CI: assert `site/src/lib/rate_card.v2.json` == `pricing/rate_card.v2.json`.  
3. Generated or test-asserted MCP catalogue from the Python tool list (or a
   shared JSON inventory).  
4. Vernacular one-pager in BRAND: Intermediate↔payg, waste check vs chaos
   governor, fail-closed scope.  
5. Add `ohm-receipt` skill mirror (or explicitly document “receipt is MCP-only”).

**Exit:** changing rate card v3 or adding a 9th tool cannot silently desync
site/docs.

### Phase 2 — Edge honesty (runtime care)

1. **Skip edge SET** when request `cache_control=no_store` **or** response
   `x-at-cache: BYPASS` (case-insensitive). Prefer BYPASS so org
   `default_cache_no_store` is honored even when the hashed body lacks
   `no_store`.  
2. Regression tests: Python + Rust path (or e2e through edge) for no_store and
   org default no_store.  
3. Soft-cap: either propagate spend-cap headers on `/internal/edge-hit` or
   document “soft warnings MISS-only” in STATUS / OPERATIONS.  
4. Readiness: non-dev fail (or hard metric + alert) when Python is on
   MemoryStore.  
5. Optional: `resolve_tenant` must not invent `tenant_{suffix}` after Allowed —
   fail closed to proxy without caching under wrong namespace.

**Exit:** no_store and org no-store claims hold on the public edge path.

### Phase 3 — Catalogues & ops completion

1. Partner CSV: replace `[fill]` with real rows **or** mark template and stop
   claiming “20 real rows”.  
2. Bounty ops: evidence log template (receipt URL, post URL, seat email,
   credit applied).  
3. Steal-kit / GAP checklists: close or explicitly defer open items.  
4. INSPECTION.md: add rows for edge no_store, MCP count, rate-card site sync.  
5. README: kill personal Windows path; point to AGENTS.md for cloud native run.

**Exit:** distribution artefacts are either real or labeled templates.

### Phase 4 — Deliberate dual audience (product care)

1. Indie surfaces (home, demo, bounty, Forum, r/cursor): waste check + Pro+
   burn → Intermediate.  
2. Enterprise / directory / marketplace: chaos governor → design partner /
   enterprise apply.  
3. Header CTA doctrine written once: guest “$0 seat” is **conversion**; hero
   “waste check” is **belief**. Cross-link both; do not pretend they are the
   same job.  
4. Align AGENTS.md / README metaphor (tollbooth vs pipe) with BRAND lead.

**Exit:** a stranger can tell which story a page is telling in one screen.

---

## 7. Acceptance — “care bar”

The product passes the care bar when:

1. **Hostile FAQ:** every Tier-1/2 siege reply matches code + OPERATIONS.  
2. **Count honesty:** MCP tool count, meter prices, commit tiers appear once
   as SoT and everywhere else by import/test.  
3. **Funnel honesty:** public-key demo cannot imply bounty eligibility.  
4. **Policy honesty:** `no_store` / org default no-store hold through the edge.  
5. **Degraded honesty:** MemoryStore, Unverified, empty edge secret, Stripe
   unsynced are named in STATUS/OPERATIONS, not discovered in an incident.  
6. **Channel honesty:** blocked channels stay blocked in every leftover title.  
7. **Catalogue honesty:** partner CSV / steal-kit / readiness checkboxes
   reflect reality, not aspiration.

---

## 8. Work order (when executing)

Prefer this sequence so each merge is reviewable:

| Step | Phase | Primary files |
|------|-------|---------------|
| A | 0 | `SIEGE_DEFENSE.md`, `LAUNCH_POSTS.md`, MCP docs/UI, `WasteCheckClient`, READINESS/MARKETPLACE |
| B | 1 | `pricing/page.tsx`, rate-card sync test, `ohm-receipt` skill, BRAND vernacular |
| C | 2 | `gateway-rs/src/main.rs` SET gate, e2e/no_store tests, readiness MemoryStore |
| D | 3 | partner CSV policy, INSPECTION, README |
| E | 4 | nav/CTA doctrine, listings vs home copy pass |

Do **not** mix Phase 2 runtime with Phase 0 copy in one PR if avoidable —
reviewers need a clean correctness diff.

---

## 9. What “understanding it as well as you do” means here

You are not shipping a gateway feature list. You are shipping a **billable
exact-replay pipe** with:

- a **belief funnel** (waste check → receipt → bounty),  
- a **conversion funnel** ($0 Intermediate seat → MCP attach),  
- an **enterprise thesis** (chaos governor / locality / trees),  
- and an **ops honesty doctrine** (document degraded tiers; never invent green).

The care failures above are not random. They cluster where two planes meet
(Rust SET vs Python no_store), where two audiences share one header (demo vs
seat), and where catalogues are maintained by hand (seven tools, rate tables,
partner rows). The remediation program attacks those seams — not the metaphor.

---

## 10. Related docs

- [BRAND.md](BRAND.md) · [PRICING.md](PRICING.md) · [OPERATIONS.md](OPERATIONS.md)  
- [ARCHITECTURE.md](ARCHITECTURE.md) · [REDIS_MESH.md](REDIS_MESH.md) · [STATUS.md](STATUS.md)  
- [distribution/WASTE_CHECK.md](distribution/WASTE_CHECK.md) · [distribution/SIEGE_DEFENSE.md](distribution/SIEGE_DEFENSE.md)  
- [INTEGRATIONS.md](INTEGRATIONS.md) · [ENTERPRISE_CHAOS.md](ENTERPRISE_CHAOS.md)  
- Root [INSPECTION.md](../INSPECTION.md) · [AGENTS.md](../AGENTS.md)

---

*End of methodological appendix. Execution starts at Phase 0 when instructed.*
