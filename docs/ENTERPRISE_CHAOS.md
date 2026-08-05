# Enterprise chaos — withOhm as entropy organizer

Canonical enterprise thesis. Companion: [VISION.md](VISION.md) · [GEM_POSITION.md](GEM_POSITION.md).

## Thesis

Enterprises do not feel AI spend the way indie builders do. Pain is **abstracted**
into commits, shared keys, and quarterly FinOps. What they cannot ignore is
**chaos**: shadow AI, repeat inference, unsafe browse, opaque multi-vendor
bills, and client lock-in.

withOhm is the **control plane that governs that chaos** — SSO tenancy,
compliance policy, corporate clean ledger, OpenAI-compatible ingress, and the
Ohm Agent Shell. Coding agents (Cursor, Claude Code, VS Code, and friends)
attach over MCP; SDKs and the Shell use the same pipe.

## Chaos map

| Chaos | Symptom | withOhm answer |
|-------|---------|----------------|
| Repeat inference | Bill spikes, rate limits | Exact-match replay + clean ledger |
| Shadow AI | Personal keys, unmanaged tools | SSO org, enforced ingress, model allowlists |
| Unsafe browse | Scrapers, PII, legal risk | Purpose-bound compliant ingest |
| Opaque vendors | Multi-lab invoices | Cost-center attribution + FinOps export |
| Client lock-in | “We depend on one IDE” | Agent Shell + `base_url` + integrations board |
| Procurement fear | No admin / audit / DPA | Org console, audit log, enterprise pack |

## Buyers (triad)

1. **Platform / AI infra** — owns the gateway and rate limits  
2. **FinOps** — wants chargeback-ready export, not vibes  
3. **Security / Legal** — purpose-bound fetch, audit, DPA bind  

Indie design partners remain **meter proof**, not the end customer.

## Product surfaces

| Surface | Role |
|---------|------|
| `api.withohm.dev` | OpenAI-compatible pipe (BYOK or managed pool) |
| Org console (`/org`) | Members, cost centers, policy, ledger export |
| Agent Shell (`/workbench`) | Thin workbench that **must** use the Ohm pipe |
| Integrations board | Cursor, Claude Code, VS Code, Windsurf, Zed + pipe stack |

## Non-goals

- Semantic cache  
- PAYG wholesale of lab tokens on Intermediate  
- Full VS Code fork in v1 (Agent Shell + open `base_url` cover the workbench)

## Success bar

A platform lead can SSO in, mint a service key, attribute spend to two cost
centers, export a month, and show Legal a denied fetch — from the org console
and pipe, with whatever clients their teams already run.
