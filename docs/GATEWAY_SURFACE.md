# Gateway surface (Neon AI Gateway harvest)

Ohm keeps **BYOK + pipe rent**. This surface steals Neon’s packaging, not their wholesale model host.

| Surface | Endpoint / tool | Notes |
|---------|-----------------|-------|
| Public catalog | `GET /models.json` | No auth — machine-readable routes + scopes |
| Auth catalog | `GET /v1/models` | Requires `ohm:chat` |
| Scopes | `ohm:chat`, `ohm:fetch`, `ohm:admin` | Default on issue: chat+fetch. Fetch needs `ohm:fetch`. |
| Env lineage | `parent_tenant_id` + `env_label` on `POST /v1/admin/tenants` | Child inherits terms/plan; suspended parent → child 403 |
| Per-model usage | `GET /v1/usage` → `by_model` | requests + hit/miss tokens per model id |
| Env pull | `python scripts/ohm_env_pull.py` | Writes `OHM_API_KEY` / `OHM_BASE_URL` (+ optional upstream) |

## Issue a preview env key

```bash
curl -s -X POST http://localhost:8080/v1/admin/tenants \
  -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" \
  -d '{
    "plan":"payg","terms_ack":true,"dpa_ack":true,
    "parent_tenant_id":"tenant_abc123",
    "env_label":"preview",
    "scopes":["ohm:chat","ohm:fetch"]
  }'
```

## Env pull (Neon-style)

```bash
python scripts/ohm_env_pull.py --api-key sk-at-... --base-url http://localhost:8081/v1
```
