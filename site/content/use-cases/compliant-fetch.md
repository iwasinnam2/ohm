Pull public pages into agent context through the Pipeline’s compliance gate. Intent required. Policy enforced. Never “scrape everything and hope.”

## Summary

- **Public-only retrieval** — Respect robots and published purpose enums
- **Metered** — Web fetch is a first-class Stripe meter
- **Ack-bound** — Terms / DPA acknowledgements where required
- **Auditable** — Pipeline-side ingest, not a silent sidecar
- **No training claim** — Fetch feeds requests; replay inventory stays exact-match only

## Why fetch belongs on the pipe

Agents that browse off-pipe create shadow risk. Putting fetch on the same governed crossing as chat keeps FinOps and compliance in one ledger story.

## Anti-pattern: unmanaged scrapers

Keys in random workers, no purpose, no retention story, no org policy — the opposite of a chaos governor.

## How withOhm wins

Use the documented fetch / web URL fields with intent. Read [Legal & compliance](/docs/legal), [Security](/docs/security), and try the public [Fetch toy](/fetch).

## Related

[Product: Pipe](/product/pipe) · [Enterprise chaos](/use-cases/enterprise-chaos) · [Pricing](/pricing)
