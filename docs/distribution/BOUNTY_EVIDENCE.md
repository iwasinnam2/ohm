# Bounty evidence log — operator template

Manual ledger for `$100` metered-usage credit claims. There is **no**
automated grant in code — credit is applied by an operator after review.

Claims arrive at `partners@withohm.dev` with subject `Artifact bounty`.
Rules live on https://www.withohm.dev/bounty.

## Required evidence (all three)

| Field | Example |
|-------|---------|
| Receipt URL | `https://www.withohm.dev/r/…` (seat key, not public demo key) |
| Social post URL | Live public post that shares that receipt |
| Seat email | Intermediate checkout email |

Reject if: public-proof / demo key receipt · receipt alone · private / login-walled post · missing seat email.

## Log (append rows)

Copy into a private sheet or keep commits offline if emails are sensitive.
Repo copy stays empty of PII:

| date | receipt_url | post_url | seat_email | credit_applied | notes |
|------|-------------|----------|------------|----------------|-------|
| | | | | n | |

CSV mirror (header only — fill offline or in a private ops sheet):

```csv
date,receipt_url,post_url,seat_email,credit_applied,stripe_customer_or_tenant,notes
```

## Done when

- [ ] Evidence triad present
- [ ] Post is public (no login wall)
- [ ] `$100` credit applied on the Intermediate tenant
- [ ] Claimant replied with confirmation

Related: [WASTE_CHECK.md](WASTE_CHECK.md) · [/bounty](https://www.withohm.dev/bounty)
