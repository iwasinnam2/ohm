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

## OpenAI-compatible vendors (Gemini, DeepSeek, Moonshot/Kimi, Z.ai/GLM, Qwen, xAI/Grok)

Routed by model prefix to each vendor's documented OpenAI-compatible endpoint
(`gemini-*`, `deepseek-*`, `kimi-*`/`moonshot-*`, `glm-*`, `qwen*`, `grok-*`).

| Topic | Ohm posture | Operator action |
|-------|-------------|-----------------|
| BYOK-first | Customer sends their vendor key via `X-Ohm-Upstream-Key`; env keys are dev fallback / enterprise managed pool only | Confirm each vendor's ToS permits proxy/BYOK use before enabling env keys in production |
| Endpoint drift | Base URLs configurable per vendor (`{VENDOR}_BASE_URL`) | Re-verify OpenAI-compat endpoints when vendors ship API changes |
| Data residency / export | Some vendors (Moonshot, Z.ai, Qwen) operate non-US/UK regions | Check customer data-routing obligations before enabling for regulated tenants |
| Logging / retention | Same identical-request Redis cache rules as OpenAI path | Disclose subprocessors; honor `no_store` |

## Cache training hard-deny

`AT_COMPLIANCE_ALLOW_CACHE_TRAINING=false`. Any code path that bulk-exports Redis chat payloads for training must refuse when this flag is false (enforced in gateway helpers).

## Review cadence

Re-read provider ToS on each major product launch and at least quarterly.
