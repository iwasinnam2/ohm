# Ohm Terms of Service

**Version:** `tos-2026-07-26`  
**Product:** Ohm OpenAI-compatible gateway + public-web ingestion  
**Public mirror:** site `/docs/terms`  
**Contact:** partners@withohm.dev

MVP operator terms binding on `terms_ack`. Entity-specific liability caps may be amended by the deploying operator’s counsel.

## 1. Service

Ohm provides: (a) LLM request routing and identical-request cache replay; (b) optional public-web context fetch under [`docs/LEGAL.md`](../LEGAL.md). Upstream model providers (e.g. OpenAI, Anthropic) process prompts under their terms.

## 2. Accounts and keys

API keys identify a tenant. You are responsible for key custody. Suspended tenants receive HTTP 403.

## 3. Prohibited uses

You must not use the Service to:

- Access login-gated, credentialed, or private account systems
- Harvest leads, build person dossiers, or derive biometrics
- Conduct unsolicited direct marketing (email/SMS/etc.) without a lawful basis (UK PECR and equivalents)
- Violate copyright, database rights, or site terms through bulk republication of fetched content
- Attempt to extract cache contents for model training or competing model development
- Violate applicable criminal computer-misuse / unauthorized-access laws

## 4. Cache

Identical chat requests may be stored in Redis for the configured TTL solely for **identical-request replay**. Cache is not a training corpus. Use `cache_control: "no_store"` when prompts must not be written to cache.

## 5. Web ingestion

Requires `web_purpose`, `web_compliance_ack`, and (when enforced) `terms_ack` / `dpa_ack`. Fetched pages are excerpted and personal identifiers are redacted by default. Public pages only.

## 6. Customer content

You retain rights in prompts and outputs as between you and Ohm, subject to upstream provider terms. You grant Ohm a limited license to process content to provide the Service (routing, caching as configured, metering).

## 7. Subprocessors

See [`docs/SECURITY.md`](../SECURITY.md) and the DPA. Typical: model providers you enable, AWS (or equivalent host), Stripe (billing).

## 8. Fees and ledgers

Ohm invoices (Stripe) are separate from your or Ohm’s upstream provider pay-as-you-go costs. Usage meters and savings figures are **estimates** for identical-request cache effects, not guaranteed savings.

## 9. Disclaimer and liability

Service is provided as-available. Caps and exclusions: set by operator counsel for the deploying entity.

## 10. Acknowledgement

API field `terms_ack: true` (and tenant `terms_version` at key issue) means the caller accepts this version.

## Amendments (2026-08)

Additive under `tos-2026-07-26` (existing acks remain valid):

- **Operational metadata.** Optional path labels (`X-Ohm-Path` / `ohm_path`) and
  cost-center bindings are service-operation fields for hit-ratio inventory and
  FinOps attribution — not content for model training.
- **Spend caps.** Org policy may soft-throttle or hard-refuse cache **MISS**
  upstream when monthly pipe-rent caps are exceeded. Cache **HIT** replay still
  serves. Caps are not prepaid credits; Ohm invoice ≠ provider bill.
- **Savings and receipts.** Dual-ledger and public savings receipts remain
  estimates (`estimate_only`). No guaranteed savings SLA; no semantic cache;
  provider invoice reconcile is not offered.
