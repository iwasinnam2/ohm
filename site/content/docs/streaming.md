# Streaming & failover

Pre-first-byte failover is a shipped feature of the withOhm pipe. Streams stay honest under provider wobble — without pretending we can hand a live SSE session to a second upstream mid-flight.

This page is the public contract. Machine-readable refusals live on [`GET /v1/public/honesty`](https://api.withohm.dev/v1/public/honesty).

## What “failover” means here

Failover is a **sequential retry before the first committed response byte**. It is not:

- Racing two providers in parallel
- Silently switching labs mid-request
- Continuing the same client stream on a second upstream after tokens have started

Two planes cooperate:

| Plane | What it retries | When |
| --- | --- | --- |
| **Rust edge** (`api.withohm.dev` → `gateway-rs`) | Control-plane URL (`AT_RS_PRIMARY` → `AT_RS_FALLBACK`) | Connect error, or 5xx before any body byte is forwarded |
| **Python control plane** | Same resolved provider, fresh connection (one retry) | Upstream connect / HTTP error before the first SSE line |

Neither path is multi-vendor racing. `AT_FALLBACK_MODEL` is resolve-time model routing when a model cannot be served — it is **not** stream failover.

## Non-streaming

On a cache miss, the edge proxies to the control plane. If the primary fails **before** a committed successful response body, the edge retries the configured fallback URL once. Cache writes happen only after a full successful response.

Use non-streaming when the path is critical and you cannot tolerate a truncated SSE body.

## Streaming

### Pass-through shape

- **OpenAI** — SSE is passed through. The gateway sets `stream_options.include_usage=true` so the final chunk can carry `usage` for metering.
- **Anthropic** — lifecycle / `content_block_delta` events are translated on the fly into OpenAI `chat.completion.chunk` frames (not a full-buffer fake stream). Input tokens come from `message_start`; output from `message_delta`; a final usage chunk is emitted before `data: [DONE]`.
- **Edge body** — once streaming, the Rust edge pipes chunks unbuffered so tokens reach the client as the provider emits them.

### Pre-first-byte failover (shipped)

**Python:** the control plane eagerly pulls the first SSE line before returning the `StreamingResponse`. If the provider fails before emitting anything, it retries once on a fresh connection. A second failure returns an **honest non-200 HTTP status** — never a `200` stream that only carries an error frame.

**Rust:** pass-through requests fail over to `AT_RS_FALLBACK` on connect error **or** a 5xx status read before any body byte is forwarded.

Successful stream responses advertise the capability:

```http
X-Ohm-Stream-Failover: pre-first-byte
```

That header means the plane supports the contract — not that a retry fired on this request.

### After the first byte

If the upstream drops after bytes have been sent:

- The client may see a **truncated stream**
- Python may emit an in-band SSE error frame on the already-open `200` stream
- **Mid-stream provider handoff is unsupported** — the same client stream is not continued on another upstream

Plan for client reconnect, or prefer non-streaming for critical paths.

## Cache & replay on streams

Streamed and non-streamed chat share the same Redis exact-replay inventory.

| Case | Behavior |
| --- | --- |
| Stream **MISS** | Assemble only if a `finish_reason` arrived; truncated streams are never stored |
| Stream **HIT** | Cached completion replayed as synthesized SSE (`X-AT-Cache: HIT`); meters like a JSON hit |
| Timing | Replay is completion-faithful, not original chunk timing |

Edge Redis GET skips `stream=true` requests; stream HITs are served by the control plane.

## Metering

Prefer parsed `usage.total_tokens` from the stream. Fall back to a char/`4` estimate only if no usage frame arrived. Receipts and ledger rows stay estimate-honest — see [Trust](/docs/trust) and [Honesty](/docs/honesty).

## Headers you’ll see

| Header | Meaning |
| --- | --- |
| `Content-Type: text/event-stream` | SSE body |
| `X-AT-Cache: HIT` / `MISS` / `BYPASS` | Exact-replay outcome |
| `X-Ohm-Stream-Failover: pre-first-byte` | Capability: pre-first-byte retry is in force |
| `Cache-Control: no-cache` | Do not intermediate-cache the event stream |

## Verify it yourself

```bash
# Public honesty map — mid-stream handoff listed as unsupported
curl -sS https://api.withohm.dev/v1/public/honesty

# Plane readiness (non-prod surfaces also expose mvp flags)
curl -sS https://api.withohm.dev/ready
```

Look for `pre_first_byte_stream_failover` / mid-stream refusals on the honesty map. Status of public limits: [Status](/docs/status).

## Guidance for agents and CI

1. Treat a truncated stream as **incomplete** — reconnect or fall back to non-stream.
2. Critical money / write paths: prefer `stream=false` until you own reconnect logic.
3. Spiky suites still benefit from exact-replay on the next identical request once a clean `finish_reason` lands.
4. Do not assume `ohm_providers` is live failover telemetry — it reports key / route readiness, not “failover fired.”

## Related

- [Locality & edge](/product/locality) — product narrative for HIT locality + honest failover
- [Edge & Redis locality](/docs/edge) — key layout and mesh posture
- [Honesty map](/docs/honesty) — published non-goals
- [Status & limits](/docs/status)
- [Variable load](/use-cases/variable-load)
