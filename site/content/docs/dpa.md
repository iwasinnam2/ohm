# Data Processing Addendum

**Version:** `dpa-2026-07-26`  
**Product:** withOhm  
**Contact:** partners@withohm.dev

API field `dpa_ack: true` and tenant `dpa_version` at key issue bind this version.

## Roles

| Party | Role |
|-------|------|
| Customer (tenant) | **Controller** of personal data in prompts, tools, and chosen web targets |
| withOhm (operator) | **Processor** when processing that data to provide the API |
| Upstream LLM providers | **Sub-processors** (and may be independent controllers under their terms) |

## Subject matter

Processing of Customer Content submitted to `POST /v1/chat/completions` and related endpoints, including optional public-web excerpts injected as context.

## Nature and purpose

- Route requests to model providers
- Optional Redis cache for identical-request replay (TTL-bound)
- Metering aggregates (not full prompts in ledgers)
- Public-web fetch when Customer enables `fetch_web_context`

**Not in scope:** withOhm does not use Customer Content to train foundation models.

## Duration

For the subscription term; cache entries expire per configured TTL unless `cache_control: no_store`.

## Categories of data

Determined by Customer. May include account email, message content, and URLs. Account passwords are stored only as irreversible hashes. withOhm applies technical minimisation on web ingest (PII redaction, excerpt caps).

## Subprocessors

| Subprocessor | Purpose |
|--------------|---------|
| OpenAI / Anthropic (as configured) | Model inference |
| AWS (or operator host) | Compute, Redis, networking |
| Stripe | Customer billing |
| AWS Amplify (marketing/docs host) | Public documentation site |

## International transfers

If Customer Content leaves the UK/EEA, the operator documents the transfer mechanism (e.g. SCCs) before EU-scale go-live.

## Security

- Hashed Intermediate API keys at rest
- Account profiles (email + password hash) beside each apikey SHA-256 index; passwords never stored plaintext; wrapped key material used only to restore the bearer after email login
- Tenant isolation by cache key prefix
- Compliance gates on ingest

See [Security](./security).

## Customer instructions

Documented via API: purposes, acks, `cache_control`, and this DPA version.

## Acknowledgement

`dpa_ack: true` binds `dpa-2026-07-26`.

## Amendments (2026-08)

Additive under `dpa-2026-07-26`: categories of processor operations include path labels, cost-center attribution, spend-cap enforcement state, and opt-in public receipt snapshots (display name + aggregates). Customer instructs path labels via API headers / body fields. No training on Customer Content.
