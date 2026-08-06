## Hits close to the request. Failover that stays honest.

Exact-replay only pays when the GET is near the work. withOhm serves cache reads from Redis on the hot path — Python control plane and `gateway-rs` edge — so identical agent and CI traffic does not re-cross the ocean for every retry.

### What locality means here

- **Edge HIT path** — Redis GET stamped with plane/cache headers; meters HIT via the control-plane gate.
- **Pre-first-byte failover** — streams stay honest under provider wobble; mid-stream handoff is unsupported (see [Streaming](/docs/streaming)).
- **Tree-scoped keys** — `main` uses v2 keys; named trees use v3 so inventory stays partitioned under load.

### Mesh posture

Public traffic today runs on a single-region deck with a clear playbook to re-enable multi-region edges when paid volume justifies it. Operators: [Edge docs](/docs/edge).

### Variable load

Spiky CI suites and agent loops benefit most: MISS once, HIT thereafter, meters that reflect pipe rent instead of silent overspend. See [Variable load](/use-cases/variable-load).

### Related

- [Architecture](/product/architecture)
- [Streaming & failover](/docs/streaming)
- [Status & limits](/docs/status)
