# Security and trust

Ohm sits between your apps and upstream model providers. Trust boundaries below apply to the public API hostname `https://api.withohm.dev` (ACM issued; chat edge cutover separate — use local `:8081` for MVP).

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
