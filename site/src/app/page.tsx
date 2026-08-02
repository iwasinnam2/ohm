import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

const BOARD = [
  {
    href: "/workbench",
    eyebrow: "Shell",
    title: "Agent Shell",
    desc: "Thin workbench that talks only through the Ohm pipe — miss→HIT demo built in.",
    go: "Open the shell",
  },
  {
    href: "/org",
    eyebrow: "Govern",
    title: "Org & ledger",
    desc: "Cost centers, FinOps export, policy — corporate clean ledger.",
    go: "Open org console",
  },
  {
    href: "/docs/quickstart",
    eyebrow: "base_URL",
    title: "OpenAI-compatible pipe",
    desc: "Point any SDK at api.withohm.dev/v1. Keep your keys (BYOK).",
    go: "Quickstart",
  },
  {
    href: "/demo",
    eyebrow: "Proof",
    title: "60s miss→HIT demo",
    desc: "Identical call twice — watch Redis replay and the ledger tick.",
    go: "Run the demo",
  },
  {
    href: "/docs/enterprise-chaos",
    eyebrow: "Enterprise",
    title: "Chaos governor",
    desc: "SSO, audit, compliant fetch — Cursor optional.",
    go: "Read the thesis",
  },
  {
    href: "/connections",
    eyebrow: "Also",
    title: "Any client (incl. Cursor)",
    desc: "MCP attach for Cursor, Claude Code, VS Code — compatibility, not the product.",
    go: "Connect tools",
  },
] as const;

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero__lockup">
          <OhmMark className="hero__mark" />
          <h1 className="hero__brand">withOhm</h1>
        </div>
        <p className="hero__strapline">Govern AI chaos. Rent the plumbing.</p>
        <p className="hero__promise">
          Point any OpenAI-compatible client — or the Ohm Agent Shell — at one
          base URL. Exact-match prompt replay, compliant web ingest, and a
          clean ledger. Bring your own provider keys. Cursor is optional.
        </p>
        <div className="hero__cta cta-row">
          <Link href="/workbench" className="btn btn--primary">
            Open Agent Shell
          </Link>
          <Link href="/billing/intermediate" className="link-quiet">
            Get a $0 seat
          </Link>
          <Link href="/demo" className="link-quiet">
            60s demo
          </Link>
          <Link href="/billing/enterprise" className="link-quiet">
            Enterprise
          </Link>
        </div>
      </section>
      <section className="board" aria-labelledby="board-label">
        <p className="board__label" id="board-label">
          The board — pipe first, any client second
        </p>
        <ul className="board__grid">
          {BOARD.map((item) => (
            <li key={item.href}>
              <Link href={item.href} className="card card--tap">
                <p className="card__eyebrow">{item.eyebrow}</p>
                <h2 className="card__title">{item.title}</h2>
                <p className="card__desc">{item.desc}</p>
                <span className="card__go" aria-hidden="true">
                  {item.go} →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
