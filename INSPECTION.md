# Inspection manifest — claims as tests

Rule: **every public claim maps to a passing test or a golden-path step. If a
claim has no passing check, the claim comes off the site — not the other way
round.**

- Unit/integration tests: `pytest -q` (also CI on every push).
- Live reviewer path: `.\scripts\golden_path.ps1 -ApiKey sk-at-...`
  (nightly in CI: `.github/workflows/golden-path.yml`).

## Product claims

| Claim (site/docs) | Check |
|---|---|
| Dynamic model switching, one OpenAI-compatible pipe | `test_units.py::test_provider_byok_resolve`, `test_anthropic_sse.py::test_anthropic_true_stream_translation` |
| Prompt caching (identical request → cache HIT) | `test_gateway.py::test_chat_cache_hit`; golden step "chat MISS then metered cache HIT" |
| Cache HITs are metered and billed (including Rust edge HITs) | `test_money_path.py::test_edge_hit_meters_cached_tokens`; golden step "usage delta" |
| Edge HIT path enforces tenant status (suspension / caps) | `test_money_path.py::test_edge_hit_denies_suspended_tenant`, `::test_edge_hit_enforces_request_cap` |
| Edge HIT path fails safe without the shared secret | `test_money_path.py::test_edge_hit_disabled_without_secret`, `::test_edge_hit_rejects_wrong_secret` |
| SSE streaming end-to-end (progressive, not buffered) | `test_gateway.py::test_stream_meters_usage_chunk`, `test_anthropic_sse.py` (5 tests); golden step "SSE streaming pass-through" |
| Streamed responses replay from cache (miss populates, hit replays as SSE, shared entry with JSON path) | `test_stream_replay.py` (6 tests: stream→stream, stream→JSON, JSON→stream, hit metering, truncated-stream guard, round-trip) |
| Cache key v2: transport noise normalized (CRLF, outer whitespace), Python/Rust byte parity | `test_units.py::test_cache_key_v2_normalizes_transport_noise`, `::test_cache_key_v2_parity`; gateway-rs `cache_key_v2_parity_with_python` |
| Mid-stream failover | **Not claimed** — docs/STREAMING.md says unsupported |
| Compliant web browsing (purpose gates, robots fail-closed, PII redaction) | `test_compliance.py` (18 tests); golden step "compliant web fetch" |
| Copyright excerpt caps + client cannot raise worker ceiling | `test_compliance.py::test_clamp_excerpt_chars_never_raises_ceiling`, `::test_excerpt_cap_truncates` |
| Compliance policy exposes copyright posture object | `test_gateway.py::test_compliance_policy_shape` |
| SSRF: DNS re-check, private-IP deny, connect-time IP pin | `test_compliance.py::test_url_gate_dns_literal_skip_ok`, `::test_url_gate_blocks_credentials_and_login`; pin: `workers/ingest_worker.py::_pinned_get` |
| Cache never exported for training | `test_compliance.py::test_cache_training_hard_deny` |
| `cache_control: no_store` skips the cache | `test_gateway.py::test_no_store_skips_cache_write` |
| Edge skips SET on `no_store` / `x-at-cache: BYPASS` | `gateway-rs` `should_skip_edge_set` unit test |
| MCP ships exactly eight tools (incl. `ohm_receipt`) | `test_mcp_catalogue.py` |
| Site rate-card mirror == `pricing/rate_card.v2.json` | `test_rate_card.py::test_site_rate_card_copy_matches_canonical` |
| Prod `/ready` fails when Python fell back to MemoryStore | `redis.backend=memory` + non-dev region → 503 (`main.py` ready) |
| Rate limiting (RPS + burst) | `test_gateway.py::test_rate_limit_and_usage` |
| BYOK — metered tenants cannot burn platform env keys | `test_money_path.py::test_payg_cannot_burn_env_upstream_keys` |
| Terms/DPA ack required before tenant issue / web fetch | `test_gateway.py::test_issue_tenant_requires_terms_ack`, `test_compliance.py::test_terms_acks_required` |

## Billing claims

| Claim | Check |
|---|---|
| `/v1/usage` matches the Stripe invoice (ceil per 1k units) | `test_money_path.py::test_ledger_usd_matches_stripe_ceil_math`, `::test_billable_units_ceil` |
| Zero-token requests are never billed | `test_money_path.py::test_billable_units_zero_tokens_bill_nothing`, `::test_zero_tokens_never_fire_stripe` |
| Meter events are idempotent (no double-billing on retry) | `test_money_path.py::test_meter_passes_idempotency_identifier` |
| Failed meter events dead-letter and replay | `test_money_path.py::test_failed_meter_event_dead_letters_and_replays`, `::test_replay_requeues_on_persistent_failure` |
| Delinquent tenants suspend after grace | `test_money_path.py::test_delinquency_sweep_suspends_expired_tenants`, `::test_delinquency_sweep_spares_recent_delinquents` |
| Request caps enforced on chat + fetch | `test_money_path.py::test_request_cap_enforced_on_chat`, `::test_fetch_cap_429_despite_metered_spend` |
| Checkout mint is rate-limited | `test_money_path.py::test_checkout_rate_limited_after_burst` |
| Published pricing ($0 Intermediate seat, commit tiers $29/$99/$499 with included usage, Enterprise contact us) | golden step "subscriptions 200 + published pricing (rate card v2)" |
| Site, API config, and docs all quote the same rates (single canonical source) | `test_rate_card.py` (site imports `pricing/rate_card.v2.json` directly; config defaults asserted equal) |
| Commit tiers: checkout accepts tier, invoice.paid grants included usage scoped to meters | `test_money_path.py::test_checkout_passes_commit_to_session`, `::test_commit_tier_detected_from_invoice_lines`, `::test_commit_included_usd_matches_rate_card` |
| $29 one-off credit pack is retired (410 + guidance) | `test_money_path.py::test_topup_is_retired_with_commit_guidance` |
| Pricing changes follow pre-committed rules, not moods | `docs/PRICING.md` rules + weekly `.github/workflows/pricing-pulse.yml` telemetry |

## Infra claims

| Claim | Check |
|---|---|
| Public API live | golden step "api health (Rust plane)"; CI nightly |
| Single-region us-east-1 (no stale multi-region claims) | golden step "status page 200"; `infra/runbooks/SINGLE_REGION.md` |
| Redis snapshots (7-day) | Terraform `redis_snapshot_retention_days` in `infra/terraform/main.tf` |

## Operator checks (not automated)

- Stripe test-mode Checkout → key mint → first invoice preview matches
  `/v1/usage` (run `scripts/stripe_public_lifecycle.ps1`).
- MCP stdio handshake in Cursor (`ohm_chat`, `ohm_fetch_web`, `ohm_usage`) —
  the golden path exercises the same HTTP calls the tools make.
