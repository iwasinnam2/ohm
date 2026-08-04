# Ohm Data Processing Addendum

**Version:** `dpa-2026-07-26`  
**Public mirror:** site `/docs/dpa`  
**Contact:** partners@withohm.dev

MVP DPA for UK GDPR / EU GDPR alignment. Binding on `dpa_ack`.

## Roles

| Party | Role |
|-------|------|
| Customer (tenant) | **Controller** of personal data in prompts, tools, and chosen web targets |
| Ohm (operator) | **Processor** when processing that data to provide the API |
| Upstream LLM providers | **Sub-processors** (and may be independent controllers for their own purposes under their terms) |

## Subject matter

Processing of Customer Content submitted to `POST /v1/chat/completions` and related endpoints, including optional public-web excerpts injected as context.

## Nature and purpose

- Route requests to model providers
- Optional Redis cache for identical-request replay (TTL-bound)
- Metering aggregates (not full prompt storage in ledgers)
- Public-web fetch when Customer enables `fetch_web_context`

**Not in scope:** Ohm does not use Customer Content to train foundation models. `AT_COMPLIANCE_ALLOW_CACHE_TRAINING` remains `false`.

## Duration

For the subscription term; cache entries expire per `AT_CACHE_TTL_SECONDS` (default 3600s) unless `cache_control: no_store`.

## Categories of data

Determined by Customer. May include identifiers, message content, and URLs. Ohm applies technical minimisation on web ingest (PII redaction, excerpt caps).

## Subprocessors

| Subprocessor | Purpose |
|--------------|---------|
| OpenAI / Anthropic (as configured) | Model inference |
| AWS (or operator host) | Compute, Redis, networking |
| Stripe | Customer billing |

## International transfers

If Customer Content leaves the UK/EEA, operator must document transfer mechanism (e.g. SCCs). Template placeholder: document before EU go-live.

## Security

Hashed API keys at rest; tenant isolation by cache key prefix; compliance gates on ingest. See [`docs/SECURITY.md`](../SECURITY.md).

## Customer instructions

Documented via API: purposes, acks, `cache_control`, and this DPA version (`dpa_ack` / `dpa_version`).

## DPIA triggers (Customer)

Large-scale monitoring, special-category data, or systematic people-profiling via the API—Customer remains responsible for DPIA where required.

## Acknowledgement

API field `dpa_ack: true` and tenant `dpa_version` at key issue bind this version.

## Amendments (2026-08)

Additive under `dpa-2026-07-26` (existing acks remain valid):

- Categories of processor operations include path labels, cost-center
  attribution, spend-cap enforcement state, and opt-in public receipt snapshots
  (display name + aggregates). Customer instructs path labels via API headers /
  body fields. No training on Customer Content.
