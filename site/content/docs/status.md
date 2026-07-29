# Status & limits

## Service status

- **Docs / marketing:** `https://withohm.dev`
- **Status:** `https://status.withohm.dev` (Vercel → `/status`)
- **`api.withohm.dev`:** edge-pending until public API cutover; ACM issued
- **Supported edge:** local `http://localhost:8081` — control plane `GET /ready`

## Hosts

| Host | Role |
|------|------|
| `withohm.dev` | Marketing + docs |
| `api.withohm.dev` | Public API (target); ACM certificate issued |
| `status.withohm.dev` | Status page |
| Local `:8081` | Supported client entry (Rust edge) until public cutover |

## Defaults

| Limit | Default |
|-------|---------|
| Rate (requests/sec) | 20 |
| Burst | 40 |
| Cache TTL | 3600s |
| Mid-stream failover | Unsupported |
| Enterprise uptime SLA | Published under Enterprise agreements only |

## Compliance gates

| Gate | Default |
|------|---------|
| Terms / DPA ack | Required for web context + tenant issue |
| Public-only web fetch | Enforced |
| Cache → training | Forbidden |

See [Legal](./legal), [Terms](./terms), [DPA](./dpa), [Privacy](./privacy).
