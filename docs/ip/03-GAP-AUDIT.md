# Gap audit — as-implemented vs claimable (Phase A)

Honest mapping for counsel. **Claim language that overstates the code will fail enablement and credibility.**

Legend:

- **Implemented** — true in current mainline
- **Partial** — related behaviour exists; claim frame needs narrowing or engineering
- **Missing** — aspirational “strong technical character” frame under the July 2026 intermediate-step filter; would need build + evidence before filing

---

## §1 Dual-plane HIT admission FSM

### Claim frame (aspirational)

Socket-level locking state machine holding network egress buffers at the edge until an atomic inter-process handshake validates quota/rate/lease caps.

### As implemented today

| Step | Behaviour | Evidence |
|------|-----------|----------|
| 1 | Edge Redis GET by exact digest (tenant + tree + hash) | `gateway-rs` chat HIT path |
| 2 | If `AT_RS` edge secret set: HTTP `POST {primary}/internal/edge-hit` with bearer tenant token, edge secret, `total_tokens`, `model`, `request_sha256` | `edge_hit_gate` |
| 3 | Control plane: verify secret → `auth_tenant` → rate limit → meter HIT → ledger → optionally `mint_receipt` → JSON `{ok, billed_usd, receipt?}` | `edge_hit_meter` |
| 4 | Edge on **2xx**: build response headers, attach receipt header, **then** `body(cached)` | success branch ~L745–767 |
| 5 | Edge on **4xx**: relay denial body; **do not** serve cache | denial branch |
| 6 | Edge on gate unreachable / 5xx / empty secret: **full-proxy** to Python (no edge HIT serve) | `None` / empty secret |

### Gap vs claim frame

| Claim element | Status | Notes |
|---------------|--------|-------|
| Dual process (edge ↔ control plane) | **Implemented** | Clear |
| HIT serve contingent on remote admit | **Implemented** | When edge secret configured |
| Deny path without releasing cache body | **Implemented** | 4xx relay |
| “Hold egress buffers” / socket lock | **Partial / Missing** | Practically: gate await **before** response build. No explicit kernel/socket buffer lock API; body already in memory from Redis |
| “Atomic lease” / distributed lock | **Missing** | HTTP request/response; no Redis lease/fencing token on the blob |
| Mid-flight cancel if lease revoked during stream | **Missing** | Cached HIT is non-streaming full body today on edge success path |
| Gate-down behaviour | **Implemented** | Fail open to full proxy (correctness), not fail closed |

### Filing implication

Strongest **honest** claim is: *distributed admit-before-release control for content-addressed cache hits across edge and control plane, with explicit deny and fail-over transitions* — not OS-level buffer locking unless engineered.

**Gap-close if counsel needs stronger intermediate-step “network state” story:** document/implement explicit states (`LOOKUP → AWAIT_ADMIT → RELEASE | DENY | PROXY`), optional short-lived admit token bound to digest, and tests for race (concurrent HIT while suspended). Aim: features that **interact with technical subject matter** (egress control), not billing.

---

## §2 Content-addressed cache tree isolation

### Claim frame (aspirational)

DAG pointer structures isolating execution namespaces while preserving content-addressed deduplication without cross-tree key collisions.

### As implemented today

| Feature | Behaviour | Evidence |
|---------|-----------|----------|
| Trees | Tenant-scoped named namespaces; default `main` | `CacheTreeRegistry` |
| Keys | `main`: `at:{tenant}:cache:v2:{digest}`; named: `at:{tenant}:tree:{id}:cache:v3:{digest}` | `blob_key_for` |
| Fork | Creates child meta + empty local index; `parent_tree_id` set | `fork` |
| COW read | `parent_chain` walk up to depth cap; resolve digest via chain | `parent_chain` / resolve helpers |
| Index | Per-tree digest list in Redis JSON | `index_add` / `index_list` |
| Freeze | Status flag blocks writes | `freeze` / `assert_writable` |
| Exact-match only | Absolute inside a tree; no semantic | `docs/ARCHITECTURE.md`, honesty map |

### Gap vs claim frame

| Claim element | Status | Notes |
|---------------|--------|-------|
| Namespace isolation by key prefix | **Implemented** | Different Redis keys per tree |
| Parent pointer / lineage | **Implemented** | `parent_tree_id` chain (tree of trees, not blob DAG) |
| Content-addressed digests | **Implemented** | SHA-256 of canonical request |
| True shared blob store (one object, many refs) | **Partial** | Digests content-addressed; blobs may still be stored per-tree key (COW read walks parents rather than pointer-to-single-CAS object in all cases) — verify against resolve/set paths before claiming “no duplication” |
| Collision-free runtime fork algorithm | **Partial** | Fork creates empty index; collisions avoided by key layout + digest identity, not a novel hash trie |
| Ambient bleed prevention as proved invariant | **Partial** | By construction of keys + tree header; needs explicit threat model + tests for counsel |

### Filing implication

Draft as **namespaced content-addressed cache with copy-on-write lineage resolution**, not a novel memory allocator / DAG filesystem unless the shared-CAS model is tightened and tested.

---

## §3 Deterministic Ed25519 receipt handshake

### Claim frame (aspirational)

Inline cryptographic protocol binding request digest, execution telemetry, and tenant identity into a signed payload **prior to socket release**.

### As implemented today

| Feature | Behaviour | Evidence |
|---------|-----------|----------|
| Algorithm | Compact JWS, EdDSA / Ed25519 | `receipts.py` |
| Payload | `request_sha256`, `tokens_replayed`, `pipe_usd`, `tenant_sha256` (truncated fingerprint), `model`, `plane`, `region`, optional `tree_id` | `mint_receipt` |
| Edge path | Minted **inside** `edge_hit_meter` **before** HTTP response to edge; edge attaches `X-Ohm-Receipt` then returns body | gate then headers then body |
| Python HIT path | Receipts also used on control-plane HITs (same module) | `main.py` + receipts |
| JWKS | Receipt public key in `/.well-known/http-message-signatures-directory` with Web Bot Auth key | JWKS handler |
| Optional | Disabled if `AT_RECEIPT_ED25519_SEED_B64` unset | env |

### Gap vs claim frame

| Claim element | Status | Notes |
|---------------|--------|-------|
| Bind digest ↔ telemetry ↔ tenant fingerprint | **Implemented** | In JWS payload |
| Sign before client sees body (edge path) | **Implemented** | Order: admit+mint → headers+body. Not a separate TCP “hold,” but causal order is correct |
| Bind to “meter ledger mutation” cryptographically | **Partial** | Meter/ledger happen in same handler before mint; receipt includes `pipe_usd` but not a ledger tx id / hash chain |
| Non-repudiation of admit decision as distinct claim | **Partial** | Receipt kind `cache_hit`; does not explicitly encode “admit=allow” or rate-limit epoch |
| Mandatory (always on) | **Missing** | Optional via env — for patent, describe both modes; prefer claiming the protocol when enabled |

### Filing implication

Honest strong frame: *method of minting a verifiable Ed25519 receipt that binds exact-replay request digest to hit telemetry and tenant fingerprint as a precondition of releasing a dual-plane cache-hit response.*  
Avoid claiming a novel signature algorithm (Ed25519/JWS are known); novelty must sit in **what is bound and when in the dual-plane release sequence**.

---

## Summary for counsel

| Mechanism | Closest honest technical story | Biggest gap to aspirational “technical character” language |
|-----------|--------------------------------|------------------------------------------------------------|
| HIT admission | Admit-before-release across planes + deny/proxy FSM | OS “buffer lock” / atomic lease |
| Cache trees | COW namespaced CAS keys + lineage walk | True single-blob DAG memory manager |
| Receipts | Pre-release JWS binding digest↔telemetry↔tenant | Ledger tx hash chain; mandatory always-on |

**Recommendation into Phase B:** Ask counsel which of these **honest** stories retain technical character through the **Pozzoli intermediate-step filter** (UKIPO July 2026 PN) and remain non-obvious. If all Red, **Do not file**.
