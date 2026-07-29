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
| `/` | Hero: Ω + withOhm + Explore Subscription |
| `/docs` | Doc index |
| `/docs/[slug]` | Curated markdown from `content/docs/` |
| `/subscriptions` | Free trial · Intermediate · Enterprise |
| `/design-partners` | Founding design-partner apply (Resend → admin) |
| `/billing` | Redirects to `/subscriptions` |
| `/billing/intermediate` | Intermediate checkout |
| `/billing/enterprise` | Enterprise application |

## Deploy

```bash
cd site
npx vercel --prod --yes
```
