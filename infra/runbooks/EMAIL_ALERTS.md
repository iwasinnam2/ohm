# Email alerts — paused until revenue

SNS email notifications are **off**. Alarms and topics stay; only the
mailbox delivery is stopped. Resume when revenue covers watching inbox noise.

There is no SES in this stack. The only AWS email paths were SNS
`protocol = "email"` subscriptions on two topics.

| Topic | Managed by | Email endpoint |
|-------|------------|----------------|
| `ohm-alerts` | Terraform (`infra/terraform/alerts.tf`) | `admin@withohm.dev` when `enable_email_alerts=true` |
| `withohm-budget-alerts` | Console only ([BUDGETS.md](BUDGETS.md)) | was `admin@withohm.dev` |

Slack (Observer / Chatbot) is unaffected. Route53 health checks are also
unaffected — those are a separate always-on cost; this runbook does not
tear them down.

## Do this now (live account — not terraformed from CI)

Until the next `terraform apply` lands, delete the live email subscriptions
in the console so mail stops immediately:

1. SNS → Topics → `ohm-alerts` → **Subscriptions** → delete every
   `Protocol = email` row (keep the topic; Chatbot/Slack may still use it).
2. SNS → Topics → `withohm-budget-alerts` → same: delete email
   subscriptions only.
3. Optional CLI (us-east-1, account `594161136574`):

```powershell
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:us-east-1:594161136574:ohm-alerts --region us-east-1
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:us-east-1:594161136574:withohm-budget-alerts --region us-east-1
# For each SubscriptionArn with Protocol email:
aws sns unsubscribe --subscription-arn SUBSCRIPTION_ARN --region us-east-1
```

Budget email is console-only — Terraform never owned that subscription, so
step 2/3 is the whole fix for spend alerts.

## Terraform (keeps email from coming back)

`enable_email_alerts` defaults to `false`, so `aws_sns_topic_subscription.ohm_alerts_email`
has `count = 0`. After merge, apply so state drops the subscription:

```powershell
cd infra/terraform
terraform plan  # expect: destroy aws_sns_topic_subscription.ohm_alerts_email
terraform apply
```

Do **not** set `enable_email_alerts = true` in `terraform.tfvars` until you
intentionally resume.

## Resume later

1. In `terraform.tfvars`: `enable_email_alerts = true` (and `alert_email` if
   not the default `admin@withohm.dev`).
2. `terraform apply` — AWS emails a confirmation link; click it.
3. Console: on `withohm-budget-alerts`, **Create subscription** → Protocol
   `Email` → `admin@withohm.dev` → confirm the link.
4. Tick the confirm steps back in [BUDGETS.md](BUDGETS.md) / [GO_LIVE.md](GO_LIVE.md).

## Not in scope here

- **Resend** on Amplify (`RESEND_API_KEY`) — product form mail, not AWS billing.
  Blank the Amplify env var if you also want those paused.
- **Stripe** failed-payment emails — Stripe Dashboard, not AWS.
- **Route53 health checks** — still probing; disable separately if Cost
  Explorer shows them as the real bill.
