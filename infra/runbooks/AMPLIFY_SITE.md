# Amplify Hosting — withOhm site

Marketing Next.js app in `site/` deploys via **AWS Amplify Hosting** (`WEB_COMPUTE` SSR).

## Create / update (CLI)

App already created:

| Field | Value |
|-------|--------|
| App ID | `d136djyswic57f` |
| Default domain | `https://d136djyswic57f.amplifyapp.com` |
| Feature branch URL | `https://cursor-mesh-phase3-5-prod.d136djyswic57f.amplifyapp.com` |
| Platform | `WEB_COMPUTE` |
| SSR role | `arn:aws:iam::594161136574:role/AmplifySSRServiceRole-withohm` |

```powershell
# Redeploy feature branch
aws amplify start-job --app-id d136djyswic57f --branch-name cursor/mesh-phase3-5-prod --job-type RELEASE --region us-east-1

# Or master (after merge)
aws amplify start-job --app-id d136djyswic57f --branch-name master --job-type RELEASE --region us-east-1
```

Set secrets in Amplify Console → Environment variables (do **not** commit):

| Key | Value |
|-----|--------|
| `RESEND_API_KEY` | Resend key for `/api/*/apply` |
| `API_EDGE_LIVE` | `1` (already set) |
| `OHM_API_URL` | `https://api.withohm.dev` (already set) |

Build spec: repo-root [`amplify.yml`](../amplify.yml) with `appRoot: site`.

**Next.js:** Amplify Hosting compute supports through **Next.js 15** — the marketing app is pinned to `next@15.5.9` for SSR (`deploy-manifest.json`). Do not bump to Next 16 until Amplify documents support.

## Custom domain

After first green deploy on `https://master.<appId>.amplifyapp.com` or the feature branch URL:

1. Amplify Console → Domain management → add `withohm.dev` + `www` + optional `fetch.withohm.dev`
2. Update GoDaddy CNAMEs from Vercel → Amplify DNS records
3. `fetch.withohm.dev` → same Amplify app (middleware rewrites `/` → `/fetch`)
4. See [APEX_CUTOVER.md](runbooks/APEX_CUTOVER.md) (replace Vercel targets)

Optional env: `OHM_DEMO_API_KEY` — dedicated public-proof tenant key. Powers
`/api/public-fetch` (live Ohm pipe) and `/api/demo-session` (zero-friction
`/demo` waste check, mock-only). Do not use a paying customer key.

**SSR gotcha:** Amplify does not inject branch env vars into Next.js API routes
unless the build writes them into `site/.env.production`. That is done in
repo-root [`amplify.yml`](../amplify.yml) (`env | grep -e OHM_DEMO_API_KEY …`).
After changing env vars, push a commit or run a full RELEASE so the build
re-runs with the new values.

## Cost (ballpark)

Amplify Hosting build minutes + SSR compute + request/data transfer — typically low tens of USD/mo at launch traffic; watch Amplify + CloudWatch billing alarms.
