# Security and trust

Ohm sits between your apps and upstream model providers. Trust boundaries below apply to the public API hostname `https://api.withohm.dev`. Local smoke: `http://localhost:8081`.

**Legal operating bounds for web ingestion and adjacent frameworks are mandatory.** See [LEGAL.md](LEGAL.md), [legal/TERMS_OF_SERVICE.md](legal/TERMS_OF_SERVICE.md), and [legal/DPA.md](legal/DPA.md).

## What is cached

Identical chat completion requests (per tenant) may store the model response in Redis for the configured TTL. Cache keys are derived from tenant + model + messages (+ web-fetch extras including `web_purpose`).

Web-context payloads are built only after compliance gates (purpose, acks, URL policy, robots, copyright excerpt caps, PII redaction). Cache writes are skipped when `cache_control` is `no_store`. Cache purpose is identical-request replay only — never training.

## Retention

- Default TTL: `AT_CACHE_TTL_SECONDS` (3600 locally).
- Ledger counters persist for metering/billing; they are aggregates, not full prompts.
- Ingested markdown is not retained as a long-lived people database—fetch is request-scoped into the prompt/cache key path only.
- Opt-out: contact support for no-store tenants (enterprise) or use unique nonces in messages when you must bypass cache.

## Web ingestion trust rules

- Public `http`/`https` only.
- No embedded credentials, session tokens, or private-network targets.
- Login/account/private API path fragments are rejected.
- `robots.txt` honored by default (`OhmBot` user agent).
- Emails/phones/ID-like strings redacted by default before model injection.
- `GET /v1/compliance/policy` exposes the live policy to authenticated clients.

## Subprocessors

- Model providers you enable (e.g. OpenAI, Anthropic)
- Amazon Web Services (compute, Redis, networking)
- Stripe (customer billing)

## Keys

- Customer keys are stored hashed (SHA-256) at rest.
- Bootstrap env keys (`AT_API_KEYS`) are for local/dev only.
- Suspended tenants receive HTTP 403 with a clear message.

## Cursor Directory / MCP plugin surface

Listing: Open Plugins package under `.cursor-plugin/` (stdio MCP + skills).

| Rule | Behavior |
|------|----------|
| Transport | **Local stdio only** — no remote MCP URL, no always-on reverse shell |
| Secrets | `OHM_API_KEY` / `OHM_UPSTREAM_KEY` via env variable placeholders only — never hardcoded in `mcp.json` |
| Bootstrap | `sk-at-dev` is rejected when `OHM_BASE_URL` points at `api.withohm.dev` |
| BYOK | Upstream provider key rides `X-Ohm-Upstream-Key` per request; not persisted by Ohm |
| Legal acks | Bound at Checkout / tenant mint — MCP tools do **not** forge `terms_ack` / `dpa_ack` |
| Web fetch | Public http(s) only; robots fail-closed; PII redaction; purpose gate |
| Error bodies | MCP client redacts responses that look like they contain key material |
| Install | `pip install withohm-mcp` then `ohm-mcp` on PATH |

Reviewer packet: [listings/DIRECTORY_VERIFICATION.md](listings/DIRECTORY_VERIFICATION.md).

## Amendments (2026-08) — path, spend caps, receipts

| Surface | Behavior |
|---------|----------|
| `X-Ohm-Path` | Optional frequency-farm label (normalized `[a-z0-9_-]{1,64}`); echoed on responses; stored on ledger events |
| Spend-cap headers | Soft mode: `X-Ohm-Spend-Cap: soft` + `X-Ohm-Spend-Cap-Usd` on allowed MISS; hard mode: `402` `spend_cap_exceeded` |
| Clean ledger | Events include `path` (default `default` if absent); hit-ratio APIs group by cost center or path |
| Public receipts | Threat model unchanged — unguessable token, no prompts, display name + aggregates only |

## Amendments (2026-08) — cache trees (Phase 0)

| Surface | Behavior |
|---------|----------|
| `X-Ohm-Cache-Tree` | Optional exact-replay tree (`[a-z0-9_-]{1,64}`); header wins over body `cache_tree`; default `main`; invalid → `400` |
| Key layout | `main` → `at:{tenant}:cache:v2:{digest}` (unchanged); named → `at:{tenant}:tree:{id}:cache:v3:{digest}` |
| Isolation | Trees never cross tenants; exact-match only inside a tree — not a semantic cache, not a DB branch |
| Training | Unchanged hard deny — trees are still identical-request replay only ([CACHE_TREES.md](CACHE_TREES.md)) |
