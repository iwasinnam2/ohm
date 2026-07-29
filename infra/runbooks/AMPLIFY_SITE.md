# Amplify Hosting — withOhm site

Marketing Next.js app in `site/` deploys via **AWS Amplify Hosting** (`WEB_COMPUTE` SSR).

## Create / update (CLI)

```powershell
# One-time: connect GitHub (needs a PAT with repo scope)
$token = gh auth token
aws amplify create-app `
  --name withohm-site `
  --platform WEB_COMPUTE `
  --repository https://github.com/iwasinnam2/ohm `
  --access-token $token `
  --region us-east-1 `
  --environment-variables API_EDGE_LIVE=1,OHM_API_URL=https://api.withohm.dev,RESEND_FROM="withOhm Applications <partners@withohm.dev>"

# Note appId from output, then:
aws amplify create-branch --app-id <APP_ID> --branch-name master --region us-east-1
aws amplify start-job --app-id <APP_ID> --branch-name master --job-type RELEASE --region us-east-1
```

Set secrets in Amplify Console → Environment variables (do **not** commit):

| Key | Value |
|-----|--------|
| `RESEND_API_KEY` | Resend key for `/api/*/apply` |
| `API_EDGE_LIVE` | `1` |
| `OHM_API_URL` | `https://api.withohm.dev` |

Build spec: repo-root [`amplify.yml`](../amplify.yml) with `appRoot: site`.

## Custom domain

After first green deploy on `https://master.<appId>.amplifyapp.com`:

1. Amplify Console → Domain management → add `withohm.dev` + `www`
2. Update GoDaddy CNAMEs from Vercel → Amplify DNS records
3. See [APEX_CUTOVER.md](runbooks/APEX_CUTOVER.md) (replace Vercel targets)

## Cost (ballpark)

Amplify Hosting build minutes + SSR compute + request/data transfer — typically low tens of USD/mo at launch traffic; watch Amplify + CloudWatch billing alarms.
