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

After first green deploy on `https://master.<appId>.amplifyapp.com`:

1. Amplify Console → Domain management → add `withohm.dev` + `www`
2. Update GoDaddy CNAMEs from Vercel → Amplify DNS records
3. See [APEX_CUTOVER.md](runbooks/APEX_CUTOVER.md) (replace Vercel targets)

## Cost (ballpark)

Amplify Hosting build minutes + SSR compute + request/data transfer — typically low tens of USD/mo at launch traffic; watch Amplify + CloudWatch billing alarms.
