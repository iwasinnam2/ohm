## Hits close to the request. Failover that stays honest.

Exact-replay only pays when the GET is near the work. withOhm serves cache reads from Redis on the hot path — Python control plane and `gateway-rs` edge — so identical agent and CI traffic does not re-cross the ocean for every retry.

Streaming is a first-class path on that same pipe: OpenAI SSE pass-through, Anthropic→OpenAI chunk translation, and **pre-first-byte failover** when the upstream dies before the first token. Mid-stream handoff to a second provider is intentionally unsupported — see the full contract on [Streaming & failover](/docs/streaming).

### What locality means here

- **Edge HIT path** — Redis GET stamped with plane/cache headers; meters HIT via the control-plane gate.
- **Pre-first-byte failover** — sequential retry before any body byte is committed; honest HTTP error if both attempts fail (never a `200` stream of only an error frame).
- **Tree-scoped keys** — `main` uses v2 keys; named trees use v3 so inventory stays partitioned under load.

### Streaming on the hot path

| Shipped | Not shipped |
| --- | --- |
| Pre-first-byte retry (Rust URL + Python same-provider) | Mid-stream provider handoff |
| Unbuffered SSE pipe at the edge | Parallel multi-provider race |
| Stream HIT replay as synthesized SSE | Faithful original chunk timing |

Capability header on stream responses: `X-Ohm-Stream-Failover: pre-first-byte`.

### Mesh posture

Public traffic today runs on a single-region deck with a clear playbook to re-enable multi-region edges when paid volume justifies it. Operators: [Edge docs](/docs/edge).

### Variable load

Spiky CI suites and agent loops benefit most: MISS once, HIT thereafter, meters that reflect pipe rent instead of silent overspend. See [Variable load](/use-cases/variable-load).

### Related

- [Streaming & failover](/docs/streaming) — full public contract
- [Architecture](/product/architecture)
- [Edge & Redis locality](/docs/edge)
