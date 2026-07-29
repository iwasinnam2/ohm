# Upstream provider checklist

Operator runbook before enabling a provider in production. Re-check when provider ToS change.

## OpenAI

| Topic | Ohm posture | Operator action |
|-------|-------------|-----------------|
| API resale / passthrough | Gateway is OpenAI-compatible proxy | Confirm current ToS allows your commercial model |
| Logging / retention | Ohm may cache identical responses in Redis | Prefer customer `no_store` for sensitive tenants; disclose in DPA |
| Training on API data | Ohm does **not** train on prompts; disable any export-to-train path | Confirm OpenAI API data-usage settings for your org |
| Abuse / prohibited uses | Mapped in Ohm compliance + customer ToS | Keep abuse reporting contacts current |
| Rate limits | Token bucket per tenant | Size quotas so upstream bans are unlikely |

## Anthropic

| Topic | Ohm posture | Operator action |
|-------|-------------|-----------------|
| Commercial API use | Claude models via gateway when key configured | Confirm API Terms for your entity |
| Safety / prohibited uses | Customer ToS + purpose gates | Align refusals with Anthropic usage policy |
| Logging | Same cache rules as OpenAI path | Disclose subprocessors |

## Cache training hard-deny

`AT_COMPLIANCE_ALLOW_CACHE_TRAINING=false`. Any code path that bulk-exports Redis chat payloads for training must refuse when this flag is false (enforced in gateway helpers).

## Review cadence

Re-read provider ToS on each major product launch and at least quarterly.
