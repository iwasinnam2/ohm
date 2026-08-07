# Copyright & database rights

**Version:** `copyright-2026-08-07` · Contact: [partners@withohm.dev](mailto:partners@withohm.dev) (subject `Copyright`)

> Not legal advice. Excerpt caps are technical minimisation — not a fair-use
> opinion or license to republish.

## Posture

withOhm fetches **public** pages for short, purpose-bound context. We do **not**
own that third-party content. We do **not** offer a bulk republication or
training-corpus API. Cache is **identical-request replay only**.

| Control | What it does |
|---------|----------------|
| Per-source / total char caps | Truncate long pages before injection |
| Large code-block stripping | Omit oversized fenced/indented code |
| Operator ceiling | Clients cannot raise caps above the server limit |
| robots / 402 / 401 / 403 | Honored — no auto-pay, no evasion |
| No cache training | Env hard-deny; never a training export |

## You must not

- Bulk-republish fetched pages or build a scrape-to-site mirror via Ohm
- Use fetch outputs or cache contents to train or improve models
- Bypass paywalls, robots denials, or 402 licensed-crawl gates

## Rights-holder notice

Email **partners@withohm.dev** with subject `Copyright`, identification of the
work and URLs, and your authority to act. Hosted service: acknowledge within
3 business days; may suspend keys or refuse further fetches where appropriate.

## Related

[Legal & compliance](/docs/legal) · [Terms](/docs/terms) · [DPA](/docs/dpa) ·
[Privacy](/docs/privacy) · Policy API: `GET /v1/compliance/policy`
