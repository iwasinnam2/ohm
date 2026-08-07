# Invention disclosure — withOhm / Ohm (counsel draft)

**Classification:** Attorney work product draft. Architecture details below largely already appear in public docs (`ARCHITECTURE.md`, `CACHE_TREES.md`); this file organizes them for **patent counsel**, not as marketing.  
**Not a patent application. Not legal advice.** Do not mark “patent pending” until counsel files.  
**Inventors:** _[legal names — fill before filing]_  
**Assignee / applicant:** _[legal entity — fill]_  
**First public disclosure (approx.):** open GitHub repo + `www.withohm.dev` documentation in 2026 — confirm exact dates for grace-period analysis.

---

## 1. Problem field

LLM applications and coding agents re-issue **byte-identical** (or mechanically identical) chat completion requests. Upstream token billing charges again. Existing “AI gateways” typically:

- Proxy and log without exact-replay economics, or
- Offer **semantic** / embedding similarity caches that change answers and raise compliance risk, or
- Bundle managed model margins instead of metering a neutral pipe.

Operators also need **branchable** replay inventory for CI/PR agents without cloning database branching products, and **purpose-gated** public-web fetch that is not a lead-harvest scraper.

## 2. Concise invention summary

A **metered AI traffic utility** (“tollbooth”) that:

1. Serves OpenAI-compatible chat at an edge that performs **content-addressed exact-match** lookup (digest of canonical model + messages + selected extras).
2. On **HIT**, replays the stored completion **without** calling an upstream model lab, and meters the crossing as pipe rent / savings — not as model wholesale.
3. On **MISS**, routes to BYOK or configured upstream, stores the completion blob under the digest, and meters accordingly.
4. Partitions replay inventory into **named cache trees** (branchable exact-replay namespaces) orthogonal to durable governance (auth, Stripe meters, compliance, receipts).
5. Optionally injects **public-web context** only through a compliance gate (allowed purposes, URL gate, robots, PII redaction, excerpt/copyright caps) with explicit acks — refusing login-gated and dossier-style uses.
6. Emits **honest** cache / plane headers and optional cryptographic receipts so HIT claims are auditable.

Slogan form (non-claim): *Neon branches state. Labs discount prefixes. Ohm branches exact replay — and the pipeline bills the crossing.*

## 3. Candidate inventive concepts (for counsel to claim / discard)

Counsel should search prior art (semantic LLM caches, CDN response caches, API gateways, Redis request caches, prompt caches from labs). Likely **combination / system** claims rather than “caching HTTP” alone.

| # | Concept | Distinguishing notes |
|---|---------|----------------------|
| A | Dual-container split: **Ephemeral Side** (exact-replay blobs + trees + edge HIT) vs **Pipeline System** (tenancy, Stripe meters, compliance ingest, trust/receipts) meeting at a named HIT/MISS crossing | Separates replay inventory from billing/policy truth |
| B | **Cache trees**: named namespaces over content-addressed digests (`main` v2 keys; named trees v3); fork / promote / freeze / reset as operations on exact-replay inventory — **not** Postgres WAL branching and **not** semantic cache | CI compose with external DB branches via headers only |
| C | Metering model: pipe rent on crossings; HIT = zero upstream tokens; dual ledger / savings **estimates**; spend caps that refuse MISS upstream but still serve HIT | Economic object is the crossing |
| D | Purpose-enumerated **compliant public-web retrieval** bound into the same pipe (acks + URL/robots/PII/excerpt enforcement) with `no_store` for confidential prompts | Product-enforced legal surface, not post-hoc ToS only |
| E | Edge/control-plane parity: Rust edge Redis GET on HIT; Python control plane on MISS; shared tenant/bootstrap keying so cache keys align | Two-plane implementation of A |
| F | Honesty layer: cache-purpose headers limited to identical-request-replay; JWKS / receipt path so HIT is not silent theatre | Anti-fraud / auditability of replay claims |

**Non-goals (do not claim as ours / disclaim):** semantic or fuzzy cache; training on customer cache; pretending to be a model lab; Neon-compatible database branching.

## 4. System elements (reference embodiment)

```
Client (SDK / Agent / MCP)
    → Edge (gateway-rs): Redis GET by digest (+ optional tree id)
         HIT → stamp headers, meter HIT, return blob
         MISS → Primary (Python gateway): auth, policy, upstream, store blob, meter
    → Optional ingest worker: purpose-gated fetch → redacted excerpts into context
Pipeline durable: org/SSO, Stripe meters, audit, receipts
```

Digest: SHA-256 (or equivalent) over canonical serialization of model + messages + cache-relevant extras.  
Trees: `at:{tenant}:cache:v2:{digest}` vs `at:{tenant}:tree:{tree_id}:cache:v3:{digest}`.

## 5. Advantages

- Deterministic answers on HIT (exact match), avoiding semantic-cache drift.
- Cost: repeated agent loops stop paying labs for identical prompts.
- Governance: money and compliance stay off the Redis hot path.
- Composability: `X-Ohm-Cache-Tree` + external `NEON_BRANCH` (or similar) without conflating products.
- Compliance: public-web path is deny-by-default for gated/dossier uses.

## 6. Dates and evidence counsel will ask for

| Item | Where to find |
|------|----------------|
| Source embodiment | `src/at_utility/`, `gateway-rs/`, `workers/` |
| Architecture narrative | `docs/ARCHITECTURE.md`, `docs/CACHE_TREES.md` |
| Compliance enforcement | `src/at_utility/compliance/`, `docs/LEGAL.md` |
| Commercial terms | `docs/legal/TERMS_OF_SERVICE.md` |
| First commit / release dates | `git log`, GitHub releases, Amplify deploy history |
| Inventors’ contribution narrative | _[fill — who conceived dual containers, trees, metering, compliance gate]_ |

## 7. Prior art seeds (non-exhaustive — counsel expands)

- HTTP/CDN caches; Varnish; Redis response caches  
- OpenAI/Anthropic **prompt caching** (prefix discount — different economics)  
- LLM gateway products (Portkey, Helicone, LiteLLM, Cloudflare AI Gateway, etc.)  
- Semantic response caches / embedding similarity stores  
- Database branching (Neon) — related *metaphor*, different object  

## 8. Filing recommendation (operator)

1. Engage patent counsel **immediately**; run novelty / freedom-to-operate against the seeds above.  
2. Strong default for US: **provisional application** within any remaining grace period, then non-provisional / PCT per budget.  
3. Assign inventions to the operating entity; get inventor declarations.  
4. After serial number issues, record it in [IP.md](IP.md); only then consider “Patent pending” on commercial pages.  
5. Keep claim charts and office actions **out of the public repo**.

## 9. Copyright / trademark cross-link

Copyright registration and trademarks are separate — see [IP.md](IP.md) and [COPYRIGHT_REGISTRATION.md](COPYRIGHT_REGISTRATION.md). MIT license on the repository does not by itself grant your patents to licensees unless you add an express patent grant.

---

*Prepared as an internal counsel packet draft for Ohm / withOhm. Replace bracketed fields before sending.*
