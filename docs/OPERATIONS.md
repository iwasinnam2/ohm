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
