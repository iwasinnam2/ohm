# Status & limits

## Service status

- **Docs / marketing:** `https://withohm.dev`
- **Status:** `https://status.withohm.dev` (Vercel → `/status`)
- **`api.withohm.dev`:** edge-pending until [API cutover](https://withohm.dev/docs/status); ACM issued
- **API edge (MVP):** local `http://localhost:8081` — control plane `GET /ready`

## Hosts

| Host | Role |
|------|------|
| `withohm.dev` | Marketing + docs |
| `api.withohm.dev` | Public API (target); ACM certificate issued |
| `status.withohm.dev` | Status page |
| Local `:8081` | Supported MVP client entry (Rust edge) |

## Defaults

| Limit | Default |
|-------|---------|
| Rate (requests/sec) | 20 |
| Burst | 40 |
| Cache TTL | 3600s |
| Mid-stream failover | Unsupported |
| Enterprise uptime SLA | Not published for MVP (SKU text is capacity, not a contractual SLA) |

## Compliance gates

| Gate | Default |
|------|---------|
| Terms / DPA ack | Required for web context + tenant issue |
| Public-only web fetch | Enforced |
| Cache → training | Forbidden |

See [Legal](./legal), [Terms](./terms), [DPA](./dpa), [Privacy](./privacy).
