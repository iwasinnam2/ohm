## Don’t trust the savings copy. Verify the receipt.

Every cache HIT can carry a signed receipt — detached proof of what the pipe did, verifiable against a public key. Replay and audit value as an artifact, not a slogan.

### What you can verify

- **`X-Ohm-Receipt`** — Ed25519 JWS on HITs (tokens replayed, pipe USD, request digest, plane/region).
- **JWKS directory** — `/.well-known/http-message-signatures-directory`
- **Honesty map** — `GET /v1/public/honesty` — published non-goals and the endpoint that proves each item
- **Public stats** — `GET /v1/public/stats` (always `estimate_only: true`)

### What we will not claim

- Semantic / fuzzy cache
- Guaranteed savings SLAs
- Training corpus from replay inventory
- Mid-stream provider handoff

Details: [Honesty docs](/docs/honesty) · [Receipts docs](/docs/receipts) · [Trust walkthrough](/docs/trust)

### Promote, freeze, audit

Cache-tree ops emit audit events (`cache.tree_*`). Frozen tips reject writes with 409; HITs still serve. Receipts may carry optional `tree_id` / `tree_name`.

### Related

- [Architecture](/product/architecture)
- [Security](/docs/security)
- [Public receipt pages](/docs/receipts)
