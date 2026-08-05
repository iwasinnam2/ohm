# Enterprise chaos

Enterprises rarely feel AI cost the way a solo builder feels an OpenAI invoice.
Spend is buried in commits, shared keys, and quarterly FinOps reviews. What they
*do* feel is **chaos**: shadow tools, the same prompts billed twice, unsafe
browse, opaque multi-vendor bills, and teams locked to one IDE.

**withOhm is the control plane for that chaos** — one OpenAI-compatible pipe,
org SSO, compliance policy, a clean ledger by cost center, and the Agent Shell
workbench. Coding agents (Cursor, Claude Code, VS Code, and friends) plug in
over MCP when you want them; SDKs and the Shell work without them.

## The chaos map (plain language)

| What’s going wrong | What it looks like | What withOhm does |
|--------------------|--------------------|-------------------|
| **Repeat inference** | Agents retry the same prompt; bills and rate limits spike | Exact-match Redis replay + meters on HIT/MISS |
| **Shadow AI** | Personal keys, unmanaged chat tools, no allowlist | Org tenancy, SSO, enforced ingress, model policy |
| **Unsafe browse** | Scrapers stuffing junk (or PII) into prompts | Purpose-bound, robots-aware public-web ingest |
| **Opaque vendors** | Three lab invoices, no chargeback story | Cost-center ledger + monthly FinOps statement |
| **Client lock-in** | “We can only work inside one IDE” | Agent Shell + any `base_url` client |
| **Procurement fear** | No admin surface, no audit, weak DPA story | Org console, audit log, enterprise pack |

## Who buys (three chairs at the table)

1. **Platform / AI infra** — owns the gateway and rate limits; wants one pipe.
2. **FinOps** — wants chargeback-ready export (`/v1/org/ledger/statement`), not vibes.
3. **Security / Legal** — purpose-bound fetch, audit trail, Terms/DPA ack.

Indie / design-partner seats still matter: they **prove the meter**. Enterprise
is who signs the MSA.

## Product surfaces

| Surface | Role |
|---------|------|
| `https://api.withohm.dev/v1` | OpenAI-compatible pipe (BYOK or managed pool) |
| [Org console](/org) | Members, cost centers, policy, ledger / month CSV |
| [Agent Shell](/workbench) | Thin workbench that only talks through Ohm |
| [Integrations](/docs/integrations) | Cursor, Claude Code, VS Code, Windsurf, Zed, and the pipe stack |
| [Enterprise apply](/billing/enterprise) | Dedicated-pool SKU from $2,500/mo |

## API (short)

```text
POST /v1/org                              create org + bind key
GET  /v1/org/ledger                       summary + events
GET  /v1/org/ledger/statement?month=YYYY-MM
GET  /v1/org/ledger/hit-ratio?month=YYYY-MM&group_by=path|cost_center
GET  /v1/org/ledger/export?format=csv&month=YYYY-MM
PUT  /v1/org/policy                       purposes, spend caps, model allowlist
GET  /v1/org/audit
POST /v1/org/sso/dev-login                local SSO (dev secret)
```

Tag agents with `X-Ohm-Path` (docs-bot, ci-prompts, …). Org spend caps soft- or
hard-stop MISS flood per cost center; HITs still serve. FinOps stays
`estimate_only` — provider invoice import is not shipped.

Full commercial pack: repo `docs/ENTERPRISE.md`. Deep thesis: `docs/ENTERPRISE_CHAOS.md`.

## What “done” looks like for a platform lead

SSO in → mint a service key → attribute spend to two cost centers → export a
month → show Legal a denied fetch. All of that lives in the org console and the
pipe — your team’s preferred clients stay on the integrations board.

## Internal agent paths (where exact-match density is high)

These are the workloads where withOhm’s replay meter shows up fastest — the same
shapes run inside many AI-heavy companies (docs bots, support triage, preview
automation, CI prompt suites):

| Path | Why hits accumulate |
|------|---------------------|
| Docs Q&A bots | Same retrieval + answer template, many times a day |
| Support triage | Short classified prompts over recurring ticket classes |
| Branch / preview automation | Mechanical agent loops with stable tool prompts |
| CI prompt suites | Byte-identical checks on every PR |

Point those agents at the Ohm `base_url` (or attach MCP), keep prompts
byte-identical, send a stable `X-Ohm-Path`, and the ledger records HIT vs MISS
by cost center and path.
