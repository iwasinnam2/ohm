# withOhm — UK claimability brief (single attachment)

**Product:** withOhm — OpenAI-compatible exact-match replay pipe (not semantic caching)  
**Public:** [https://www.withohm.dev](https://www.withohm.dev) · open repo implements the mechanisms below  
**Instruction type:** Claimability consult only — **not** a filing instruction  
**Fee cap:** **£1,500–£2,500 + VAT** for a **1–2 page Traffic Light** opinion (Red/Amber/Green per A/B/C)  
**Overall ask:** **File** (which candidate?) or **Do not file** (defensive publication)

---

## 1. Legal frame (mandatory)

Do **not** apply the overruled *Aerotel* four-step test or AT&T/CVON signposts as the live eligibility framework.

Opine under:

- *Emotional Perception AI Ltd v Comptroller-General* **[2026] UKSC 3** (11 Feb 2026) — Aerotel abandoned; UK aligned with EPO **G1/19** (“any hardware” + intermediate step)
- **UKIPO Practice Note** *Search and Examination of UK patent applications…* (**14 July 2026**)

### Core question

> Which of our three candidate mechanisms (A dual-plane HIT FSM, B cache-tree isolation, C Ed25519 receipt handshake) retain **technical character** under the UKIPO’s July 2026 Practice Note during the **Pozzoli intermediate-step filter** — i.e. which claim features contribute to, or interact with, the technical character of the invention viewed as a whole, and survive stripping of non-technical features (metering, pipe rent, FinOps, “saving tokens”) before novelty/inventive step?

### Examination battleground (our understanding)


| Step | Hurdle                                                                               | Expectation                                                                                                 |
| ---- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1    | “Any hardware”                                                                       | **Low** — edge + control plane + Redis likely clear                                                         |
| 2    | **Intermediate step** — strip features that do not contribute to technical character | **Primary risk** — billing/metering stripped; bare hash→Redis may be non-technical or obvious once stripped |
| 3    | Novelty + inventive step (**Pozzoli**) on surviving features only                    | Commodity edge-proxy / JWS prior art applies                                                                |


---

## 2. Locked product framing

withOhm is **not** “exact + semantic caching.”


| What it is                                                           | What it is not                             |
| -------------------------------------------------------------------- | ------------------------------------------ |
| Exact-match identical-request replay (semantic = explicit non-goal)  | Fuzzy / vector / “close enough” cache hits |
| Dual-plane HIT admission before releasing cached bytes               | Free best-effort gateway cache             |
| Ed25519 HIT receipts (digest ↔ telemetry ↔ tenant fingerprint)       | Guaranteed savings SLA                     |
| Optional cache trees (COW namespaces over content-addressed digests) |                                            |


**Commercial context only (expect intermediate-step strip):** pipe rent, Stripe meters, `/v1/savings` estimates.

### Do not analyse as independent claims

- Hash LLM payload → Redis → skip upstream  
- Exact + semantic caching IAAS  
- Pipe-rent / token-cost business methods  
- Broad “AI gateway caching”

---

## 3. System sketch (HIT path)

```
Client → Rust edge :8081
           │ Redis GET (exact digest, tenant + tree)
           ├─ HIT + edge secret set
           │     → POST control-plane /internal/edge-hit
           │           (auth, rate, meter, optional mint_receipt)
           │     → 2xx: attach X-Ohm-Receipt, THEN serve cached body
           │     → 4xx: relay denial; do NOT serve cache
           │     → gate down / no secret: full-proxy to Python
           └─ MISS → Python control plane → provider BYOK → Redis SET
```

**Code anchors:** `gateway-rs` (`edge_hit_gate`); `POST /internal/edge-hit` in Python control plane; `receipts.mint_receipt`; `cache_trees` registry.

---

## 4. Candidate A — Dual-plane HIT admission FSM

**Technical problem:** Cached bytes are local at the edge; admit/deny state is non-local. Release without handshake risks serving bytes that should be denied and racing with control-plane state.

**Features hoped to survive intermediate filter:** Admit-before-release sequencing; deny without body release; gate-down full-proxy — framed as **egress / flow control**, not billing.

### As implemented (honest)


| Step | Behaviour                                                                                                 |
| ---- | --------------------------------------------------------------------------------------------------------- |
| 1    | Edge Redis GET by exact digest                                                                            |
| 2    | HTTP `POST /internal/edge-hit` with tenant bearer, edge secret, `total_tokens`, `model`, `request_sha256` |
| 3    | Control plane: secret → auth → rate limit → meter → ledger → optional receipt → JSON                      |
| 4    | Edge **2xx**: headers (+ receipt) **then** cached body                                                    |
| 5    | Edge **4xx**: denial only; no cache body                                                                  |
| 6    | Unreachable / 5xx / no secret: **full-proxy** (fail open to control plane)                                |


### Gaps vs aspirational “socket buffer lock / atomic lease” language


| Element                                              | Status                                                 |
| ---------------------------------------------------- | ------------------------------------------------------ |
| Dual plane; admit before serve; deny without release | **Implemented**                                        |
| OS/socket egress buffer lock                         | **Not implemented** — await-before-response-build only |
| Distributed lease / fencing token on blob            | **Missing**                                            |
| Mid-stream revoke                                    | **Missing** (edge HIT is full-body, non-streaming)     |


**Honest claim shape:** distributed admit-before-release for content-addressed cache hits across edge and control plane, with deny and fail-over transitions — **not** kernel buffer locking unless engineered later.

**Possible gap-close:** explicit states `LOOKUP → AWAIT_ADMIT → RELEASE | DENY | PROXY`; optional admit token bound to digest; race tests.

---

## 5. Candidate B — Content-addressed cache tree isolation

**Technical problem:** Forkable exact-replay namespaces without ambient cross-tree bleed and without full payload duplication.

**Features hoped to survive intermediate filter:** Namespace key isolation + COW parent-chain resolution as **storage/memory management**, not “git for prompts” UX.

### As implemented (honest)

- Tenant-scoped trees; default `main`  
- Keys: `at:{tenant}:cache:v2:{digest}` (main); `at:{tenant}:tree:{id}:cache:v3:{digest}` (named)  
- Fork: child meta + empty local index + `parent_tree_id`  
- COW read: walk parent chain to depth cap  
- Freeze blocks writes; exact-match only inside a tree

### Gaps


| Element                                                           | Status                                                |
| ----------------------------------------------------------------- | ----------------------------------------------------- |
| Key-prefix isolation; lineage pointers; content-addressed digests | **Implemented**                                       |
| True single shared CAS object store (one blob, many refs)         | **Partial** — verify before claiming zero duplication |
| Novel collision algorithm beyond key layout + digest identity     | **Weak / commodity**                                  |


**Honest claim shape:** namespaced content-addressed cache with COW lineage resolution — not a novel DAG filesystem unless tightened.

---

## 6. Candidate C — Ed25519 receipt handshake

**Technical problem:** Non-repudiable binding of exact-replay identity to admission outcome at the proxy crossing.

**Features hoped to survive intermediate filter:** Crypto binding of digest ↔ telemetry ↔ tenant fingerprint **before** client release (security/integrity) — not the `pipe_usd` business figure alone.

### As implemented (honest)

- Compact JWS, EdDSA / Ed25519  
- Payload includes: `request_sha256`, `tokens_replayed`, `pipe_usd`, `tenant_sha256` (truncated fingerprint), `model`, `plane`, `region`, optional `tree_id`  
- Edge path: mint inside `/internal/edge-hit` **before** response to edge; edge sets `X-Ohm-Receipt` then returns body  
- JWKS published at `/.well-known/http-message-signatures-directory`  
- Optional: disabled if receipt seed env unset

### Gaps


| Element                                                                              | Status                |
| ------------------------------------------------------------------------------------ | --------------------- |
| Bind digest ↔ telemetry ↔ tenant fingerprint; causal order before client body (edge) | **Implemented**       |
| Cryptographic bind to ledger tx id / hash chain                                      | **Partial / missing** |
| Explicit “admit=allow” field; always-on mandatory                                    | **Partial / missing** |


**Honest claim shape:** method of minting a verifiable Ed25519 receipt binding exact-replay digest to hit telemetry and tenant fingerprint as a **precondition of releasing** a dual-plane cache-hit response. Novelty is **what/when bound**, not Ed25519/JWS themselves.

---

## 7. Prior art posture (compressed)


| Cluster                                            | Role                                                                                     |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| TrueFoundry / Portkey / GPTCache (semantic)        | **Competitive contrast** for exact-only doctrine; still prior art for hash+Redis+gateway |
| Varnish / CDN / Redis / Workers / HTTP idempotency | **Fatal** to broad hash→Redis claims after filter                                        |
| LiteLLM / Helicone-class proxies                   | Commodity exact cache + routing                                                          |
| Provider prefix cache / vLLM RadixAttention        | Different layer; shows exact-sequence reuse is known                                     |
| Generic JWS / request signing / audit logs         | Must distinguish **digest↔admission↔tenant before egress**                               |
| Own site + open repo                               | **Defensive prior art** (and limits our novelty for disclosed matter)                    |


**Already public (enablement clock):** withohm.dev; GitHub implementation of edge gate, receipts, trees; architecture / receipts / cache-trees docs; honesty endpoint (exact-only non-goal).

---

## 8. Traffic Light deliverable (required)


| Light     | Meaning                                                                                                               |
| --------- | --------------------------------------------------------------------------------------------------------------------- |
| **Green** | Likely retains technical character through intermediate filter **and** plausible non-obviousness vs commodity proxies |
| **Amber** | Technical character arguable; inventive step weak without gap-close or narrowing                                      |
| **Red**   | Likely stripped as non-technical and/or obvious once filtered                                                         |


Mark **A / B / C** separately. State overall **File** (which?) or **Do not file**.

If File: rough next cost (search + drafting) and which gaps above must close first. Optionally note UK direct filing vs EP given post-2026 alignment.

**Do not** commence drafting or formal search under this instruction.

---

