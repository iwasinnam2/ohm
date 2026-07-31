import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";
import { formatUsd, getPublicStats } from "@/lib/publicApi";

const BOARD = [
  {
    href: "/connections",
    eyebrow: "Connect",
    title: "Connections",
    desc: "Cursor, Claude Code, VS Code, Windsurf, Zed — one attach, seven tools.",
    go: "Open the hub",
  },
  {
    href: "/docs/commands",
    eyebrow: "Commands",
    title: "Command catalog",
    desc: "Every MCP tool and skill, with parameters and example prompts.",
    go: "Browse the catalog",
  },
  {
    href: "/docs/optimized-usage",
    eyebrow: "Cache",
    title: "Prompt replay",
    desc: "Identical prompts replay from Redis instead of re-billing the provider.",
    go: "Run it optimized",
  },
  {
    href: "/fetch",
    eyebrow: "Fetch",
    title: "Compliant web context",
    desc: "Public pages in, redacted markdown out — robots-gated and metered.",
    go: "Try the demo",
  },
  {
    href: "/docs/pricing",
    eyebrow: "Meters",
    title: "Pipe rent",
    desc: "A $0 seat plus metered rates. You rent the plumbing, not the model.",
    go: "See the rates",
  },
  {
    href: "/status",
    eyebrow: "Grid",
    title: "Status & limits",
    desc: "Edge availability, rate limits, and provider health at a glance.",
    go: "Check the grid",
  },
] as const;

export default async function HomePage() {
  const stats = await getPublicStats();
  return (
    <>
      <section className="hero">
        <div className="hero__lockup">
          <OhmMark className="hero__mark" />
          <h1 className="hero__brand">withOhm</h1>
        </div>
        <p className="hero__strapline">Interconnectedness and accessibility.</p>
        <p className="hero__promise">
          Model switching, prompt caching and compliant web browsing — one
          OpenAI-compatible pipe. Connect it to Cursor, Claude Code, VS Code
          and more over MCP, bring your own provider keys (BYOK), and pay
          metered rates on a $0 Intermediate seat.
        </p>
        {stats && stats.estimated_upstream_avoided_usd > 0 ? (
          <p className="hero__promise">
            Tenants have avoided an estimated{" "}
            <strong>{formatUsd(stats.estimated_upstream_avoided_usd)}</strong>{" "}
            of upstream model spend via prompt replay.
          </p>
        ) : null}
        <div className="hero__cta cta-row">
          <Link href="/subscriptions" className="btn btn--primary">
            Explore subscriptions
          </Link>
          <Link href="/connections" className="link-quiet">
            Connect your tools
          </Link>
          <Link href="/billing/intermediate" className="link-quiet">
            Intermediate ($0 + meters)
          </Link>
          <Link href="/billing/enterprise" className="link-quiet">
            Enterprise application
          </Link>
        </div>
      </section>
      <section className="board" aria-labelledby="board-label">
        <p className="board__label" id="board-label">
          The board — everything, compartmentalised
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
