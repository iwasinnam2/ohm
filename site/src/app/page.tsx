import Link from "next/link";
import { CacheTreesFlowchart } from "@/components/CacheTreesFlowchart";
import { DualCrossingAid } from "@/components/DualCrossingAid";
import { OhmMark } from "@/components/OhmMark";

const PILLARS = [
  {
    title: "Zero-token replay",
    body: "Exact-replay hits answer from Redis and cost zero upstream tokens — identical requests never pay the provider twice.",
  },
  {
    title: "Cross-provider consistency",
    body: "One OpenAI-shaped pipe across OpenAI, Anthropic, Gemini, DeepSeek, Kimi, GLM, Qwen, and Grok. Keep your keys — BYOK.",
  },
  {
    title: "Locality and latency",
    body: "Cache reads on the nearest Redis edge replica; pre-first-byte failover keeps streams honest under provider wobble.",
  },
  {
    title: "Replay and audit value",
    body: "Every hit is an auditable identical-request replay with a meter you can read — never a training corpus.",
  },
];

const BOARD = [
  {
    href: "/workbench",
    eyebrow: "Shell",
    title: "Agent Shell",
    desc: "PowerShell CLI on the Ohm pipe — MCP skills and pipe cmdlets.",
    go: "Open the shell",
  },
  {
    href: "/product",
    eyebrow: "Product",
    title: "What is withOhm",
    desc: "Ephemeral replay × pipeline governance — one metered HIT/MISS crossing.",
    go: "Open the product",
  },
  {
    href: "/product/waste-demo",
    eyebrow: "Proof",
    title: "Waste demo",
    desc: "Identical agent call twice — MISS then HIT. Second call does not re-buy the model.",
    go: "Run the waste demo",
  },
  {
    href: "/product/architecture",
    eyebrow: "Deep dive",
    title: "Architecture",
    desc: "Ephemeral Side × Pipeline System — one metered HIT/MISS crossing.",
    go: "Read the architecture",
  },
  {
    href: "/use-cases/enterprise-chaos",
    eyebrow: "Enterprise",
    title: "Chaos governor",
    desc: "SSO, audit, compliant fetch — govern shadow AI and repeat spend.",
    go: "Read the solution",
  },
] as const;

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero__copy">
          <div className="hero__lockup">
            <OhmMark className="hero__mark" />
            <h1 className="hero__brand">withOhm.</h1>
          </div>
          <p className="hero__strapline">The metered pipe on wasted, repeated inference.</p>
          <p className="hero__promise">
            Agent loops re-buy the same tokens. withOhm replays identical calls
            from cache — one OpenAI-compatible pipe, BYOK, $0 Intermediate seat.
          </p>
        </div>
        <div className="hero__cta cta-row">
          <Link href="/signup" className="btn btn--primary">
            Create Account
          </Link>
          <Link href="/login" className="btn btn--login">
            Login
          </Link>
          <Link href="/i" className="link-quiet">
            Attach in Cursor
          </Link>
          <Link href="/pricing" className="link-quiet">
            Pricing
          </Link>
        </div>
        <ul className="hero__pillars">
          {PILLARS.map((pillar) => (
            <li key={pillar.title} className="hero__pillar">
              <strong className="hero__pillar-title">{pillar.title}</strong>
              <span className="hero__pillar-body">{pillar.body}</span>
            </li>
          ))}
        </ul>
      </section>

      <DualCrossingAid />

      <div className="ohm-flow--home">
        <CacheTreesFlowchart />
      </div>

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
