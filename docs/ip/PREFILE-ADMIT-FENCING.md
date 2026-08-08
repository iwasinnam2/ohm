# Pre-filing: digest-bound HIT admit fencing (A4)

**Status:** Engineering for **File-lean** bifurcation. Default **off**
(`AT_ADMIT_FENCING=false` / `AT_RS_ADMIT_REQUIRE=false`).

**Disclosure:** Prefer counsel review before blogging a deeper protocol RFC.
Code in-repo is enablement; this note is the claim-oriented summary for the
attorney pack — not a Show HN / marketing surface.

## Problem

Cached bytes sit at the edge; admit/deny state is non-local. A 2xx from
`/internal/edge-hit` must not be reusable after expiry or across digests, and
two concurrent HIT admits on the same digest must not both RELEASE.

## Mechanism (shipped, flag-off)

1. Control plane (after auth + rate limit): mint HMAC token
   `ohm_admit.v1.{payload}.{mac}` bound to `tenant`, `digest` (`request_sha256`),
   `exp`, `jti`, keyed by `AT_EDGE_SHARED_SECRET`.
2. Acquire Redis/Memory `SET NX` lease `admit:{tenant}:{digest}` for the gate
   call duration (released in `finally`) — fences concurrent in-flight admits.
3. Response includes `admit_token` when fencing is on.
4. Rust edge (`AT_RS_ADMIT_REQUIRE=1`): verify MAC + digest + **tenant** + exp
   **before** attaching body; failure → DENY without completion body.

## Env

| Env | Plane | Default | Meaning |
|-----|-------|---------|---------|
| `AT_ADMIT_FENCING` | Python | false | Mint token + take lease on `/internal/edge-hit` |
| `AT_ADMIT_TOKEN_TTL_SECONDS` | Python | 15 | Token lifetime |
| `AT_ADMIT_LEASE_TTL_SECONDS` | Python | 8 | Lease TTL safety net if process dies mid-gate |
| `AT_RS_ADMIT_REQUIRE` | Rust | false | Require valid `admit_token` before RELEASE |

## What this is not

- Not OS socket buffer locking (Tranche 3 / A3 — deferred).
- Not mid-stream revoke (Tranche 3 / A6 — needs streaming edge HIT).
- Not a substitute for the Ed25519 **receipt** (audit proof); admit token is
  **egress fencing** between planes.
