# Status & limits

## Service status

- **Docs / marketing:** `https://www.withohm.dev` (AWS Amplify + CloudFront)
- **Status:** `https://status.withohm.dev` → `/status`
- **`api.withohm.dev`:** live public API (EKS + Global Accelerator)
- **Fetch toy:** `https://fetch.withohm.dev` — demo HTML strip (not the full compliance pipe)
- **Local edge (dev):** `http://localhost:8081`

## Hosts

| Host | Role |
|------|------|
| `www.withohm.dev` | Marketing + docs (prefer until apex 301 is live) |
| `withohm.dev` | Apex — forward to www when DNS cutover complete |
| `api.withohm.dev` | Public API |
| `fetch.withohm.dev` | Public fetch demo |
| `status.withohm.dev` | Status page |
| Local `:8081` | Dev client entry (Rust edge) |

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
| Public-only web fetch | Enforced on the Ohm API pipe |
| Cache → training | Forbidden |

See [Legal](./legal), [Terms](./terms), [DPA](./dpa), [Privacy](./privacy).
