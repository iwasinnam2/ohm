# Ohm Privacy Policy (operator template)

**Effective:** 2026-07-26  
**Contact:** partners@withohm.dev

Public mirror: site `/docs/privacy`. Controllers remain responsible for their use cases.

## Roles

| Party | Role |
|-------|------|
| Tenant | Controller of prompts and chosen web targets |
| Ohm | Processor for routing, optional cache replay, metering, optional public-web context |
| Upstream LLM providers | Sub-processors for inference |

## Processing

API keys (hashed), request metadata, prompts/completions as needed to fulfill the API, optional public-web excerpts (minimised), Stripe billing identifiers.

Redis cache is identical-request replay only — not a training corpus.

## Rights and contact

UK GDPR / EU GDPR / CCPA rights as applicable: partners@withohm.dev
