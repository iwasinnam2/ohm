# withOhm site

Marketing + docs front door for **withOhm** (`https://withohm.dev`).

## Develop

```bash
cd site
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Design tokens

Visual decisions live in [`src/app/globals.css`](src/app/globals.css):

| Layer | Examples |
|-------|----------|
| Primitives | `--space-1`…`--space-10` (8px grid), `--text-xs`…`--text-hero`, copper/ink palette |
| Semantic | `--bg`, `--fg`, `--muted`, `--accent`, `--measure*` |
| Component | `--btn-padding-*`, shared `.cta-row` / `.btn--primary` / `.link-quiet` |

Doctrine checklist when changing UI: one focal point (squint), three type levels, gaps on the space scale, one primary CTA per section.

## Routes

| Path | Purpose |
|------|---------|
| `/` | Hero — compliant fetch for agents + install line |
| `/i` | Meme install URL (deeplink + share line) |
| `/fetch` | Public fetch toy (`fetch.withohm.dev` rewrite) |
| `/templates` | cursor-agent-with-web steal page |
| `/bounty` | $100 usage-credit artifact bounty (social post URL required) |
| `/docs` | Doc index |
| `/docs/[slug]` | Curated markdown from `content/docs/` |
| `/subscriptions` | Intermediate · Enterprise |
| `/login` | Log in — restore `sk-at-…` key in this browser |
| `/signup` | Sign up — $0 Intermediate seat (Stripe) |
| `/design-partners` | Founding design-partner apply (optional icing) |
| `/billing` | Redirects to `/subscriptions` |
| `/billing/intermediate` | Intermediate checkout (same form as Sign up) |
| `/billing/enterprise` | Enterprise application |
| `/billing/success` | Add to Cursor + teammate share line |

## Deploy

AWS Amplify (`WEB_COMPUTE`) — see [`../infra/runbooks/AMPLIFY_SITE.md`](../infra/runbooks/AMPLIFY_SITE.md).
