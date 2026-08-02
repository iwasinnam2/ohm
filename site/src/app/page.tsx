import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

const BOARD = [
  {
    href: "/workbench",
    eyebrow: "Shell",
    title: "Agent Shell",
    desc: "Thin workbench on the Ohm pipe — miss→HIT demo built in.",
    go: "Open the shell",
  },
  {
    href: "/docs/integrations",
    eyebrow: "Connect",
    title: "Integrations",
    desc: "Cursor, Claude, VS Code, Windsurf, Zed — and the pipe stack, interlinked.",
    go: "Open the board",
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
    href: "/org",
    eyebrow: "Govern",
    title: "Org & ledger",
    desc: "Cost centers, FinOps export, policy — corporate clean ledger.",
    go: "Open org console",
  },
  {
    href: "/docs/enterprise-chaos",
    eyebrow: "Enterprise",
    title: "Chaos governor",
    desc: "SSO, audit, compliant fetch — govern shadow AI and repeat spend.",
    go: "Read the guide",
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
        <p className="hero__strapline">Interconnectedness and accessibility.</p>
        <p className="hero__promise">
          Model switching, prompt caching, and compliant web browsing — one
          OpenAI-compatible pipe. Connect Cursor, Claude Code, VS Code, and
          more; bring your own provider keys (BYOK); pay metered rates on a $0
          Intermediate seat. Or open the Agent Shell and stay on the pipe.
        </p>
        <div className="hero__cta cta-row">
          <Link href="/billing/intermediate" className="btn btn--primary">
            Start now — $0 seat
          </Link>
          <Link href="/docs/integrations" className="link-quiet">
            Integrations
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
