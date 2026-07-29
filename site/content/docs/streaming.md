# Streaming & failover

## Non-streaming

On failure before a committed successful response body, the edge retries the configured fallback upstream. It does not race providers in parallel.

## Streaming

- OpenAI SSE is passed through.
- Anthropic events are translated to OpenAI chunk frames.
- Mid-stream provider handoff (continue the same client stream on another upstream) is unsupported.
- If the upstream connection drops after bytes have been sent, the client receives a truncated stream.
