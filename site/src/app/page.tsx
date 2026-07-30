import Link from "next/link";
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

export default function HomePage() {
  return (
    <section className="hero">
      <div className="hero__lockup">
        <OhmMark className="hero__mark" />
        <h1 className="hero__brand">withOhm</h1>
      </div>
      <p className="hero__promise">
        Exact-replay hits that cost zero upstream tokens. Cross-provider
        consistency. Locality — Redis edge reads. Replay and audit value.
        Change one base URL (or one Cursor attach) and rent the plumbing, not
        the model.
      </p>
      <div className="hero__cta cta-row">
        <Link href="/subscriptions" className="btn btn--primary">
          Explore subscriptions
        </Link>
        <Link href="/billing/intermediate" className="link-quiet">
          Intermediate ($0 + meters)
        </Link>
        <Link href="/billing/enterprise" className="link-quiet">
          Enterprise application
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
  );
}
