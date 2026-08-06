## One crossing. Two kinds of truth.

withOhm splits AI traffic control into two containers. Clients talk to one OpenAI-compatible ingress. Every request meets a named crossing — **HIT or MISS** — that is metered and, on HIT, receipted.

<!-- ohm:dual-crossing -->

### Ephemeral Side

Hot exact-replay: edge HITs, cache trees, content-addressed blobs, request context, BYOK. Optimized for latency and mechanical repeat. Can TTL, freeze, or tear down without losing the company’s durable record.

### Pipeline System

Durable governance: tenant keys and org SSO, meters → ledger → Stripe, compliance ingest, provider route honesty, JWKS receipts, org policy, audit, FinOps. Defines who may cross, what a crossing costs, and what claims we stand behind.

### Fence

Neon (Lakebase Postgres) splits ephemeral **compute** from durable **storage** so database state can branch. withOhm splits ephemeral **exact-replay inventory** from a durable **governance pipeline** so mechanical AI repeats can be isolated and billed. Neon branches state. Labs discount prefixes. Ohm branches exact replay — and the pipeline bills the crossing.

### Read deeper

- [Architecture docs](/docs/architecture)
- [Edge & Redis mesh](/docs/edge)
- [Trust & receipts](/product/trust)
- [What is withOhm](/product/what-is-withohm)
