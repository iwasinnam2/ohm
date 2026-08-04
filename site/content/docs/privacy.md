# Privacy Policy

**Product:** withOhm (OpenAI-compatible gateway)  
**Effective:** 2026-07-26  
**Contact:** partners@withohm.dev

This policy describes how withOhm processes information when you use the API and related sites. It is the operator privacy policy for the withOhm service. It is not a substitute for counsel review of your own use case.

## Roles

| Party | Role |
|-------|------|
| You (tenant) | Controller of prompts, tools, and any personal data you submit or ask withOhm to fetch |
| withOhm | Processor of that data to provide routing, optional cache replay, metering, and optional public-web context |
| Upstream model providers | Sub-processors for inference under their terms |

## What we process

- API authentication material (keys stored hashed)
- Request metadata needed to route, rate-limit, and meter (tenant id, model, token/usage counters)
- Prompt and completion content as required to fulfill `POST /v1/chat/completions`
- Optional public-web page excerpts when you enable `fetch_web_context` (minimised / redacted by default)
- Billing identifiers via Stripe when you use paid plans

We do **not** use Customer Content to train foundation models. Redis cache is for identical-request replay only (`X-AT-Cache-Purpose: identical-request-replay`).

## Cache and retention

- Default cache TTL: configured by operator (`AT_CACHE_TTL_SECONDS`, typically 3600s)
- Opt out of cache writes with `cache_control: "no_store"`
- Ledger counters are aggregates for metering, not full prompt archives

## Web retrieval

Public `http`/`https` pages only. Login-gated, credentialed, or private targets are refused. See [Legal & compliance](./legal) and the [DPA](./dpa).

## Subprocessors

Typical: OpenAI and/or Anthropic (as you enable), Amazon Web Services (or host), Stripe (billing). Details: [Security](./security) and [DPA](./dpa).

## Your rights

Depending on UK GDPR / EU GDPR / CCPA applicability, you may have rights of access, deletion, and restriction. Controllers remain responsible for data subject requests regarding content they submit. Contact partners@withohm.dev for operator requests about account/metering data.

## Cookies / marketing site

The marketing site is documentation plus self-serve billing. No advertising trackers are required for core docs. Hosting (AWS Amplify / CloudFront) may process standard request logs.

## Changes

Material changes bump the policy date and, where API acks are versioned, related terms/DPA versions.

## Amendments (2026-08)

- **Path and cost center.** We process optional traffic path labels and cost-center identifiers, plus spend-cap evaluation state, as operational metadata on the clean ledger.
- **Public receipts.** Opt-in public receipts expose a chosen display name and aggregate savings metrics only — never prompts or completions. Receipt tokens expire (≈90 days TTL).
- **Ledger retention.** Append-only ledger events are retained for billing / FinOps export under configured store bounds; they are not a training corpus.
