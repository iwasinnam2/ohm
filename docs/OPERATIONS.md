# Operations — cloud/local boundary

withOhm runs entirely in the cloud. The local machine is only needed for the
intentional operator actions listed at the bottom; if it is off or offline,
nothing about the production experience changes.

## What runs where

| Surface | Where | How it ships |
| --- | --- | --- |
| Marketing site (`www`, `status`, `fetch` hosts) | AWS Amplify (WEB_COMPUTE) + CloudFront | Amplify builds automatically on every push to `master` |
| Public API (`api.withohm.dev`) | EKS `at-utility-eks` (us-east-1) behind an NLB | GitHub Actions `Deploy API` workflow (see below) |
| Redis (cache, meters, rate limits) | ElastiCache `at-utility-redis-leader` (us-east-1) | Terraform |
| Stripe webhooks / metering | Hit `api.withohm.dev` directly | — |
| Quota allotment cron | In-cluster CronJob | Part of the k8s manifests |

## Spend caps and audit (ops)

Org hard/soft spend caps emit audit actions `org.spend_cap_hard` /
`org.spend_cap_soft`. Soft MISS responses include `X-Ohm-Spend-Cap` headers.
Caps meter **pipe rent** for the current UTC month per cost center — not
provider invoices. Hit-ratio reads: `GET /v1/org/ledger/hit-ratio`.

## Shipping the API from anywhere (no local tooling)

`.github/workflows/deploy.yml` runs on pushes to `master` that touch `src/`,
`workers/`, `gateway-rs/`, the root `Dockerfile`, or `pyproject.toml` — and can
be triggered manually from the GitHub Actions tab (workflow_dispatch).

It authenticates to AWS with OIDC — no stored AWS keys:

- IAM role `ohm-github-deployer` trusts only `repo:iwasinnam2/ohm:ref:refs/heads/master`
  (defined in `infra/terraform/cicd.tf`).
- Permissions: push to the three `at-utility/*` ECR repos + `eks:DescribeCluster`.
- Inside the cluster, an EKS access entry maps the role to group `ohm-deployers`,
  bound to a namespace-scoped Role in `at-utility` (roll deployments only — no
  delete, no cluster admin; RBAC in `infra/k8s/manifests.yaml`).

The workflow builds the three images tagged with the git SHA (ECR tags are
immutable), pushes, `kubectl set image` on `gateway`, `gateway-rs`, and
`ingest-worker`, waits for the rollouts, then curls
`https://api.withohm.dev/health`.

Note: image tags in `infra/k8s/manifests.yaml` are a bootstrap snapshot; the
live tag after any CI deploy is the git SHA. Check with
`kubectl -n at-utility get deploy -o wide`.

## Always-on alerting

Route53 health checks probe `api.withohm.dev/health` and `www.withohm.dev/`
every 30 seconds from AWS's checker fleet. CloudWatch alarms (`ohm-api-down`,
`ohm-www-down`) email **admin@withohm.dev** via the SNS topic `ohm-alerts` on
failure and on recovery (defined in `infra/terraform/alerts.tf`).

One-time setup: the SNS email subscription must be confirmed from the
admin@withohm.dev mailbox (AWS sends a confirmation link on `terraform apply`).

A nightly reviewer smoke (`.github/workflows/golden-path.yml`) also walks the
public surfaces; add the `OHM_GOLDEN_PATH_KEY` repo secret (a test-tenant API
key) to exercise the keyed money-path steps.

## Safe-by-default site

The site's billing proxy route (`/api/billing/checkout`) defaults to
`https://api.withohm.dev` when `OHM_API_URL` is unset, so a missing
env var can never point production at a loopback address.

## Remaining intentional local/operator actions

These are the only things that still require a person with credentials — by
design, not by accident:

1. **Terraform applies** (`infra/terraform/`) — infra changes, secret-adjacent
   resources. State is in the configured backend; any machine with AWS creds
   works.
2. **Secret rotations** — Secrets Manager values and the `AT_RS_EDGE_SECRET`
   Kubernetes secret. For the live Stripe key specifically: roll it in the
   dashboard, then run `scripts/rotate_stripe_key.ps1` (hidden prompt — the
   key never touches chat, shell history, or disk; verifies against Stripe,
   patches the cluster, restarts, and smoke-tests live checkout).
3. **GoDaddy DNS flip** — pointing `api.withohm.dev` CNAME directly at the
   us-east-1 NLB (then final Global Accelerator teardown). See
   `infra/runbooks/SINGLE_REGION.md`.
4. **Stripe dashboard changes** — prices, meters, webhook endpoints. At
   launch: run `scripts/stripe_create_prices_v2.sh` against live mode, set the
   `STRIPE_PRICE_*` / `STRIPE_PRICE_COMMIT_*` envs on the cluster, activate
   Stripe Tax + origin address then set `STRIPE_AUTOMATIC_TAX=true`, and add
   the `STRIPE_PULSE_KEY` repo secret (restricted read-only key) for the
   weekly pricing pulse.
5. **PyPI publishes** of the `withohm-mcp` package (`scripts/sync_ohm_mcp.ps1`).
   Note: `ohm-mcp` on PyPI is an unrelated third-party project — the console
   script is still `ohm-mcp`, only the distribution name differs.

## Edge cache tier (Redis TLS)

The Rust edge RESP client supports TLS (`rediss://…` or `AT_RS_REDIS_TLS=true`
with bare `host:port`) via rustls + webpki-roots (`gateway-rs/src/resp.rs`).

**Activate edge HITs in production:**

1. Point `AT_RS_REDIS` at the ElastiCache **reader** endpoint as
   `rediss://<reader-host>:6379` (GET path).
2. Point `AT_RS_REDIS_WRITE` at the **primary** as `rediss://<primary-host>:6379`
   (SET path; defaults to read addr if unset).
3. Ensure `AT_EDGE_SHARED_SECRET` matches Python so `POST /internal/edge-hit`
   meters HITs.
4. Roll the edge deployment; confirm `X-AT-Cache: HIT` from the edge plane
   header and the metered edge-HIT golden smoke against production.

Until secrets are updated, black-holed `127.0.0.1:9` keeps the edge in
**Unverified** auth → full-proxy to Python (correctness/billing intact;
edge latency optimization dormant). Fail-closed edge auth on Redis outage
must never return — that turned a cache-tier blip into a total API outage.

## Region posture (pre-committed, like the pricing rules)

Production is deliberately single-region (us-east-1). Multi-region carries a
~$150+/mo infrastructure floor and was torn down (Global Accelerator gone,
mesh paused not deleted — `infra/runbooks/` has the revival runbooks and the
Redis Global Datastore design). The decision to expand is pre-committed so it
never becomes a mood:

- **Trigger (either):** sustained MRR >= $500 for two consecutive months, or
  a paying tenant whose workload demonstrably suffers cross-Atlantic p95 and
  says so.
- **Action:** revive the eu-west edge per the runbooks — Rust edge + Redis
  replica first (read path only), full control-plane replication only behind
  further revenue.
- **Until then:** latency for far-away callers is what it is; do not spend
  ahead of demand. If a cheap win is wanted, CloudFront in front of the NLB
  (~$0 idle) is the only pre-approved experiment, and only after verifying
  SSE passthrough on a staging distribution — never risk the live checkout
  path for a latency shim.
