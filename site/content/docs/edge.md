# Edge & Redis locality

How cache GETs stay close to the request. Product narrative: [Locality & edge](/product/locality).

## Hot path

- **Python control plane** — full governance; Redis GET/SET for inventory and meters.
- **`gateway-rs` edge** — Redis GET on the HIT path; HIT metering gated by the control plane so the edge never holds the receipt signing key.

## Key layout

- Default tree `main`: `at:{tenant}:cache:v2:{digest}`
- Named tree (`X-Ohm-Cache-Tree`): `at:{tenant}:tree:{tree_id}:cache:v3:{digest}`

Digest = SHA-256 of the canonical request. See [Cache trees](/docs/cache-trees).

## Mesh posture

Public deck is single-region today with a documented playbook to re-enable multi-region edges when volume justifies it. Streaming failover scope: [Streaming](/docs/streaming).

## Operator pointers

Env patterns and phase table live in the repository runbooks (`docs/REDIS_MESH.md`). Status of public limits: [Status](/docs/status).
