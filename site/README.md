# Ohm site

Marketing + docs front door for **Ohm** (`api.withohm.dev` on Vercel while design iterates).

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
| `/` | Hero: Ω + promise + design-partner CTA |
| `/docs` | Doc index |
| `/docs/[slug]` | Curated markdown from `content/docs/` |
| `/design-partners` | Design-partner offer |

## Deploy

```bash
cd site
npx vercel --prod --yes
```
