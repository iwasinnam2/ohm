import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Changelog",
  description:
    "withOhm changelog — cache trees, Product and Solutions surfaces, pricing, and trust tooling.",
};

type Entry = {
  date: string;
  title: string;
  body: string;
  links?: { href: string; label: string }[];
};

const ENTRIES: Entry[] = [
  {
    date: "2026-08-06",
    title: "Resources spine",
    body: "Public Resources hub with Changelog, Security marketing page, and Contact (enterprise inquiry). Header exposes Resources alongside Product · Solutions · Docs · Pricing. Blog and case studies still deferred.",
    links: [
      { href: "/resources", label: "Resources" },
      { href: "/security", label: "Security" },
      { href: "/contact", label: "Contact" },
    ],
  },
  {
    date: "2026-08-06",
    title: "Product, Solutions, Architecture docs, Pricing",
    body: "Public Product and Use-cases filetree (Neon-shaped, Ohm nouns), Architecture docs group, and a first-class /pricing page. Header exposes Product · Solutions · Docs · Pricing.",
    links: [
      { href: "/product", label: "Product" },
      { href: "/use-cases", label: "Solutions" },
      { href: "/pricing", label: "Pricing" },
    ],
  },
  {
    date: "2026-08-06",
    title: "Main-Pudding live chrome",
    body: "Homepage atmosphere: true-black velvet, purple accent shader, graphite pipe tracks with sporadic payloads, dual-crossing aid and cache-trees flowchart on Home.",
    links: [{ href: "/", label: "Home" }],
  },
  {
    date: "2026-08-06",
    title: "Cache trees Phase 0–2",
    body: "X-Ohm-Cache-Tree select, fork / reset / promote / freeze APIs, COW reads, receipt tree claims, and /docs/cache-trees with flowchart. Neon branches state; Ohm branches exact-replay inventory.",
    links: [
      { href: "/docs/cache-trees", label: "Cache trees docs" },
      { href: "/product/cache-trees", label: "Product" },
      { href: "/use-cases/inventory-per-tenant", label: "Inventory per tenant" },
    ],
  },
  {
    date: "2026-07",
    title: "Railgun public pipe",
    body: "Public API on api.withohm.dev, Intermediate $0 seat + meters, signed HIT receipts, honesty map, Agent Shell, and BYOK OpenAI-compatible chat.",
    links: [
      { href: "/docs/quickstart", label: "Quickstart" },
      { href: "/docs/trust", label: "Trust" },
      { href: "/docs/honesty", label: "Honesty" },
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className="marketing-article">
      <header className="page-head">
        <p className="marketing-article__eyebrow">Resources</p>
        <h1>Changelog</h1>
        <p>
          What shipped on the pipe and the site. Not every commit — the releases
          that change how you build or buy.
        </p>
      </header>
      <ol className="changelog-list">
        {ENTRIES.map((entry) => (
          <li key={entry.date + entry.title} className="changelog-list__item">
            <time className="changelog-list__date" dateTime={entry.date}>
              {entry.date}
            </time>
            <h2 className="changelog-list__title">{entry.title}</h2>
            <p className="changelog-list__body">{entry.body}</p>
            {entry.links ? (
              <p className="changelog-list__links cta-row">
                {entry.links.map((link) => (
                  <Link key={link.href} href={link.href} className="link-quiet">
                    {link.label}
                  </Link>
                ))}
              </p>
            ) : null}
          </li>
        ))}
      </ol>
      <p className="marketing-article__back">
        <Link href="/resources">All resources →</Link>
      </p>
    </div>
  );
}
