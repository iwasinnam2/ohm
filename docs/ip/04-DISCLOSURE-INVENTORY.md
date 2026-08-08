# Disclosure inventory (own prior art clock)

Anything listed here is treated as **already available to the public** for novelty analysis. Prefer filing (if any) only on **unpublished** improvements that close gaps in [03-GAP-AUDIT.md](03-GAP-AUDIT.md).

## Public surfaces

| Surface | What it discloses |
|---------|-------------------|
| https://www.withohm.dev | Exact-replay product; ephemeral × pipeline; zero-token replay; BYOK; cache trees marketing |
| GitHub `iwasinnam2/ohm` (this repo) | Full implementation of edge gate, receipts, trees, metering |
| `docs/ARCHITECTURE.md` | Ephemeral Side vs Pipeline System; exact-match absolute; no semantic cache |
| `docs/CACHE_TREES.md` | Fork / promote / freeze; COW; non-goals |
| `docs/RECEIPTS.md` | HIT receipt purpose and verify story |
| `docs/REDIS_MESH.md` | Dual-plane Redis / key parity |
| `docs/distribution/SIEGE_DEFENSE.md` | Competitive contrast vs LiteLLM/Helicone/Portkey/provider cache |
| Site docs mirrors under `site/content/docs/` | Same architecture/receipts/trees/honesty |
| `GET /v1/public/honesty` | Machine-readable non-goals including exact-only |

## Enabling detail already in code (high enablement)

- `gateway-rs/src/main.rs` — full HIT admit sequence and fail-open proxy
- `src/at_utility/main.py` — `/internal/edge-hit` meter + receipt mint
- `src/at_utility/receipts.py` — full JWS payload fields
- `src/at_utility/cache_trees.py` — fork/COW/freeze/index
- `src/at_utility/cache.py` — canonical SHA-256 hashing rules

## Still relatively soft / ops (candidate trade secrets)

Do **not** publish casually if counsel later wants a narrow filing on gap-closes:

- Production edge-secret rotation runbooks beyond what’s in `docs/OPERATIONS.md`
- Any **unpublished** admit-token / lease / fencing design (gap-close for FSM)
- Any **unpublished** single-CAS blob store redesign (gap-close for trees)
- Receipt key seeds and infra credentials (always secret)

## Freeze rule (until Phase B binary)

Counsel briefs are **sent** (Phase B in flight). File-lean (~80%) engineering
may land **flag-off** admit fencing in-repo; keep blog/Show HN RFCs quiet.

1. Do not blog deeper protocol RFCs that invent new unpublished mechanisms beyond what is already in code + `PREFILE-ADMIT-FENCING.md`.
2. Safe to keep marketing on exact-replay × pipeline (already public).
3. Tranche 1 dual-use hardening may ship publicly.
4. Defensive publication tag: follow [DEFENSIVE-PUBLICATION.md](DEFENSIVE-PUBLICATION.md) only on Do-not-file / post-priority (~20% track).

## Dated snapshot (optional defensive publication)

If Phase B = **Do not file**, see [DEFENSIVE-PUBLICATION.md](DEFENSIVE-PUBLICATION.md). **Not done.**

## Pre-filing engineering (File-lean)

- [PREFILE-ADMIT-FENCING.md](PREFILE-ADMIT-FENCING.md) — A4 admit token + lease (flag-off)
