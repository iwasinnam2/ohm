# Prior-art contrast (counsel one-pager)

## What we exit (not clones of exact-only doctrine)

| Source | Discloses | Role vs withOhm |
|--------|-----------|-----------------|
| TrueFoundry AI Gateway | Exact SHA of request params + semantic (last-message cosine); Redis; governance | **Competitive contrast** — they push semantic for hit rate; we forbid semantic for determinism. Still prior art for hash+Redis+gateway |
| Portkey | Simple (exact) then semantic fallback | Same |
| GPTCache (Zilliz) | Multi-stage exact + embedding + similarity + storage + eviction | Literature prior art for hybrid pipelines |

## What still kills broad claims

| Source | Why fatal to broad claims |
|--------|---------------------------|
| Classic HTTP / CDN / Varnish / Redis response caches | Hash or key → serve cached body |
| LiteLLM / Helicone-class proxies | Exact/body cache + routing + observability |
| OpenAI / Anthropic prompt caching | Provider prefix discount (different layer, but “reuse matching tokens to save cost” narrative) |
| vLLM RadixAttention / SGLang | Exact prefix → KV reuse at engine layer |
| Generic API gateway + quota check before response | Admit/deny before serve is ordinary |

**Examiner story post-[2026] UKSC 3:** “Any hardware” clears easily. At the **intermediate step**, metering/pipe-rent/savings features are stripped as non-technical. Remaining “hash LLM JSON → Redis → skip provider” then fails **Pozzoli inventive step** against commodity HTTP/Redis/edge caches (and may itself be characterised as non-technical information retrieval).

## Where narrow claims might live (not “cleared”)

| Mechanism | Crowded art to distinguish |
|-----------|----------------------------|
| Dual-plane HIT admission | Edge + control plane; quota before cache serve; circuit breakers — must claim **specific** sync/failure semantics, not “two services” |
| Cache trees | Git COW, content-addressed stores (CAS), Redis namespacing, Neon-style branching analogies — must claim **isolation algorithm** for exact-replay digests |
| Ed25519 receipts | JWS, request signing, audit logs, Web Bot Auth / HTTP message signatures — must claim **binding of digest ↔ admission outcome ↔ tenant fingerprint before egress** |

## Own publication (defensive and clock)

Already public: www.withohm.dev, this open repository, `docs/ARCHITECTURE.md`, `docs/RECEIPTS.md`, `docs/CACHE_TREES.md`, honesty endpoints.  
→ Blocks competitors from owning the disclosed workflow; also limits our own novelty for anything already enabled in public code/docs. See [04-DISCLOSURE-INVENTORY.md](04-DISCLOSURE-INVENTORY.md).
