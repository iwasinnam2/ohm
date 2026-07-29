# Streaming / failover contract

Honest limits for Ohm’s edge. Mid-stream provider handoff without a client reconnect is **not** shipped.

## Non-streaming completions

1. Client calls Rust on port 8081 (or Python on 8080 directly); documented public entry is `https://api.withohm.dev/v1` after AWS cutover (MVP: local `:8081`).
2. Rust computes a cache key from the raw request body and `GET`s Redis **only when** `stream` is false and `fetch_web_context` is not set. Web-enriched chats always proxy to Python so injection runs before the control-plane cache key.
3. On miss, Rust proxies to Python (`AT_RS_PRIMARY`, then `AT_RS_FALLBACK` if the primary fails before a successful body).
4. Python may call OpenAI or Anthropic; on success it stores the JSON response in Redis (key = hash of **post-injection** messages) and meters a cache miss.
5. Rust may also store the response under its body-hash key for subsequent edge hits (non-web only).

Failover for non-streaming is **before** a committed successful response body. It is not a guarantee of dual-provider racing.

## Streaming completions

- **OpenAI**: pass-through SSE. The gateway sets `stream_options.include_usage=true` so the final chunk carries `usage` for metering.
- **Anthropic**: Python translates `content_block_delta` / lifecycle events into OpenAI `chat.completion.chunk` frames on the fly (no full-buffer fake stream). Input tokens come from `message_start`; output tokens from `message_delta`; a final usage chunk is emitted before `data: [DONE]`.
- **Metering**: prefer parsed `usage.total_tokens` from the stream; fall back to a char/`4` estimate only if no usage frame arrived.
- If the upstream drops mid-stream, the client may see a truncated stream. **Mid-stream handoff to a second provider without client reconnect is not implemented.** Prefer non-streaming for critical paths until that work ships.

## Operator rule

Run `scripts/release_smoke.ps1` after every Compose or image change. Do not deploy to Amazon Web Services if that script fails for reasons other than known upstream quota or billing outages.
