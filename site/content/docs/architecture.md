# Architecture

Inside withOhm: ephemeral exact-replay and a durable pipeline, connected by the crossing.

Product narrative with schematics: [Product — Architecture](/product/architecture). This page is the methodical cut — how the two containers fit, what each owns, and how a request crosses.

## Top-level overview

Instead of treating an AI gateway as a single opaque proxy tied to one vendor’s session, withOhm splits AI traffic control into two independent containers: an **Ephemeral Side** and a **Pipeline System**. Clients — Agent Shell, SDKs, MCP, CI — talk to one OpenAI-compatible ingress. The two containers meet on every request at a named crossing: **HIT or MISS**. That crossing is metered. On HIT, it can also be receipted.

This separation is what makes exact-replay economically and operationally real. Inventory can be forked, isolated, and promoted without pretending to be a database. Money, policy, and compliance can stay durable without sitting on the Redis hot path.

You will notice the same request shape you already use. What changes is where responsibility lives after the bytes leave your client.

- **Ephemeral Side** — optimized for latency and mechanical repeat. Content-addressed completions, cache trees, edge GET. This layer does not own billing truth or legal policy. It can TTL, freeze, or tear down without losing the company’s durable record.
- **Pipeline System** — optimized for correctness of *governance*: tenancy, Stripe meters, compliance ingest, provider route honesty, JWKS receipts, org audit and FinOps. This layer defines who may cross, what a crossing costs, and what claims we will stand behind.

Labs (BYOK or managed pool) remain outside both containers. Public web enters only through the Pipeline’s compliance gate. Exact-replay inventory never becomes a training corpus.

> **Note — Neon and withOhm**  
> Neon branches **database state**. withOhm branches **exact-replay inventory**. They are complementary: compose them in CI with a preview connection string and `X-Ohm-Cache-Tree`. Do not treat cache trees as Postgres branches, and do not expect a database preview to isolate mechanical prompt inventory. See [Compose with Neon](/docs/compose-neon).

## Resource hierarchy

While the sections below describe the runtime split, withOhm organizes customer resources roughly as:

| Concept | Description | Relationship |
| --- | --- | --- |
| Organization | SSO, members, policy, FinOps export | Contains tenants / keys |
| Tenant | Billing and meter identity | Owns cache trees and ledger events |
| Cache tree | Named exact-replay inventory (`main`, `pr-842`, …) | Holds digests → blobs |
| API key | Auth material (`sk-at-*` / Ohm keys) | Bound to a tenant (and optionally an org) |
| Path / cost center | Attribution labels (`X-Ohm-Path`, cost center) | Ledger dimensions — **not** cache partitions |
| Operation | Async or admin action (checkout, promote, freeze) | Audited on the Pipeline |

If you are coming from a single shared cache and a single shared bill, the hierarchy can feel like extra nouns. In practice it is how isolation and attribution stay separate: trees partition inventory; paths label spend.

## Ephemeral Side

The Ephemeral Side is where identical requests become free of upstream tokens. From the client’s perspective nothing about the OpenAI chat shape is replaced: messages in, completion out, headers for cache and billing.

What is different is what this side is responsible for. **It exists to serve and store exact-replay inventory, not to define money or law.**

### Components

- **Edge (`gateway-rs`)** — Redis GET on the hot path; stamps plane and cache headers; meters HIT only via the control-plane gate so the edge never holds the receipt signing key.
- **Content-addressed blobs** — immutable completion JSON at a digest (SHA-256 of the canonical model + messages + extras).
- **Cache trees** — named namespaces over digests. Default `main` keeps today’s v2 key layout; named trees use v3. See [Cache trees](/docs/cache-trees).
- **Request context** — BYOK header (never persisted), optional tree and path headers, `cache_control: no_store` when you must skip the write.

### How ephemeral fits into the system

When a chat request arrives:

1. The request is canonicalized and hashed inside the active tree.
2. On **HIT**, the blob is returned; the Pipeline mints meter and may mint an Ed25519 receipt. The lab is not called.
3. On **MISS**, the Pipeline routes to an upstream provider (BYOK); the completion is written into the active tree unless `no_store`.

Exact-match is absolute inside a tree. There is no semantic or fuzzy cache. Cross-tree visibility is only via explicit lineage ops (fork / promote), never ambient bleed. That is intentional: soft matching would make receipts dishonest.

Ambient note: if two agents share `main`, they are neighbors on purpose. If they should not collide, give them tips — not a second gateway.

## Pipeline System

If the Ephemeral Side is responsible for replay inventory, the Pipeline System is responsible for **who may cross, what it costs, and what we will claim in public**.

Rather than one monolith “proxy brain,” governance is composed of clear roles:

- **Auth / tenancy** — API keys, org SSO, suspension and caps
- **Meters → ledger → Stripe** — HIT / MISS / fetch; clean ledger; seat checkout
- **Compliance ingest** — purpose, robots, SSRF, PII, Web Bot Auth — before bytes reach a model
- **Provider route** — multi-vendor BYOK; pre-first-byte failover honesty (no mid-stream magic)
- **Trust** — JWKS directory, HIT receipts, published honesty map
- **Org policy / audit / FinOps** — allowlists, spend caps, export

### Correctness of claims

A HIT is not free magic. It is:

1. An identical-request replay from tenant-scoped inventory
2. A metered pipe event
3. Optionally a signed receipt verifiable against the public key directory

Savings endpoints stay `estimate_only`. The honesty map publishes non-goals so marketing cannot outrun the pipe:

```bash
curl -sS https://api.withohm.dev/v1/public/honesty
```

## HIT path: replaying without the lab

When inventory already holds the answer, the crossing stays on the Ephemeral Side and only touches the Pipeline for metering and proof.

1. **Canonicalize and hash** the request (tree-scoped key).
2. **GET** from Redis on the Ephemeral Side.
3. **Pipeline gate** records HIT meter and may mint `X-Ohm-Receipt`.
4. **Return** the blob. No upstream tokens.

You should see `X-AT-Cache: HIT` on the response. If a receipt is present, verify it yourself — [Signed receipts](/docs/receipts).

## MISS path: ask the model, then store

When inventory misses, the Pipeline owns the expensive half of the trip.

1. **MISS** on inventory.
2. **Pipeline** enforces auth, org policy, and spend caps.
3. **Upstream** generates (BYOK or managed pool).
4. **SET** into the active tree unless `no_store`.
5. **Meter** MISS (and fetch, if web context was injected earlier on the Pipeline).

Web context is never a back door around compliance: ingest runs on the Pipeline before digest and upstream. Streaming has its own honesty rules — pre-first-byte failover is shipped; mid-stream handoff is not. See [Streaming & failover](/docs/streaming).

## Durability of governance (not of every blob)

Durability in withOhm is layered on purpose. No single machine is asked to be both the hot replay path and the company’s permanent record.

- If the **edge** dies → traffic falls through to the control plane; correctness of billing stays with the Pipeline.
- If a **cache blob** TTLs → that exact-replay entry is gone unless retained (phased); meters and ledger remain.
- If **Stripe or Redis meta** is unhealthy → reconciler and honesty / ops surfaces exist so failure is visible, not vibes.
- **Retain / archive** (phased) may copy blobs off the hot path for audit — still not a training corpus, still not object storage on the HIT critical path.

The quiet implication: you can be aggressive about tip hygiene and TTL without rewriting your FinOps story every time a preview tree freezes.

## What this architecture enables

This design turns traditionally wasteful AI operations — re-paying identical agent and CI prompts, mixing preview pollution into production HIT inventory — into **inventory and metadata operations**.

- **Zero-upstream replay** — identical requests answer from Redis; the lab is not paid twice.
- **Tree-scoped isolation** — PR and agent inventories diverge without cloning tenants or databases.
- **Promote as index work** — bring new digests to `main` without rewriting history as a bulk export.
- **Compose with a database preview** — state branch + replay tip in one CI job; complementary peers.
- **Governed browse** — public web through robots / PII / SSRF before model contact.
- **Auditable claims** — receipts and honesty map bind marketing to machinery.

## In short

withOhm is an AI traffic control plane that treats:

- exact-replay inventory as **ephemeral and replaceable** (trees, TTL, edge);
- money, policy, compliance, and trust as **durable pipeline concerns**;
- the HIT / MISS crossing as the **source of economic truth** for the pipe;
- labs and the public web as **outside** systems reached only through explicit gates.

The result is infrastructure that makes mechanical AI traffic cheap to repeat, hard to lie about, and possible to attribute — without becoming a model lab and without cosplaying a database.

## Related docs

- [Cache trees](/docs/cache-trees) — branchable exact-replay inventory
- [Edge & Redis locality](/docs/edge) — hot-path GETs and mesh posture
- [Compose with Neon](/docs/compose-neon) — state branch + inventory tip
- [Streaming & failover](/docs/streaming) — pre-first-byte honesty
- [Honesty map](/docs/honesty) · [Signed receipts](/docs/receipts)
- [Product — Architecture](/product/architecture) — narrative deep dive with schematics
