# Edge & Redis locality

How cache GETs stay close to the request — and why that matters once agent and CI traffic start to spike.

Product narrative: [Locality & edge](/product/locality). Architecture context: [Architecture](/docs/architecture).

## Why locality shows up here

Exact-replay only pays when the GET is near the work. If every identical retry re-crosses a cold path for inventory that already exists, you have rebuilt the waste the pipe was meant to remove. The edge exists so HIT traffic can stay short: Redis first, meters and receipts through the control-plane gate, lab silent.

Ambient fact: locality is not a marketing region claim by itself. Public traffic today runs on a documented single-region deck, with a playbook to re-enable multi-region edges when paid volume justifies it. Honesty about mesh posture lives with the rest of the architecture — not in a slogan.

## Hot path

- **Python control plane** — full governance; Redis GET/SET for inventory and meters.
- **`gateway-rs` edge** — Redis GET on the HIT path; HIT metering gated by the control plane so the edge never holds the receipt signing key.

On a HIT, the Ephemeral Side serves the blob; the Pipeline records the crossing. On a MISS, the Pipeline owns the upstream trip. Streaming skips the edge Redis GET for `stream=true` and follows the streaming contract instead — [Streaming & failover](/docs/streaming).

## Key layout

- Default tree `main`: `at:{tenant}:cache:v2:{digest}`
- Named tree (`X-Ohm-Cache-Tree`): `at:{tenant}:tree:{tree_id}:cache:v3:{digest}`

Digest = SHA-256 of the canonical request. Named trees keep preview and agent inventory partitioned under load so `main` is not everyone’s scratch pad. See [Cache trees](/docs/cache-trees).

## Mesh posture

Public deck is single-region today with a documented playbook to re-enable multi-region edges when volume justifies it. Streaming failover scope: [Streaming](/docs/streaming). If you are designing for regional failover of the *mesh itself*, treat that as an ops roadmap item — not a silent promise of the current public cut.

## Operator pointers

Env patterns and phase table live in [docs/REDIS_MESH.md](https://github.com/iwasinnam2/ohm/blob/master/docs/REDIS_MESH.md) (source is open). Status of public limits: [Status](/docs/status). Verify plane health with `/health` and `/ready` on `api.withohm.dev`.
