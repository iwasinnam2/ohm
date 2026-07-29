import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

const QUOTES = [
  {
    quote:
      "Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.",
    attribution: "Ohm promise — design partners repeat this sentence",
  },
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero__lockup">
          <OhmMark className="hero__mark" />
          <h1 className="hero__brand">Ohm</h1>
        </div>
        <p className="hero__promise">
          Change one base URL (or one Cursor attach). Keep your keys and SDKs.
          Gain prompt replay, a clearer pipe, compliant web context — and a bill
          that rents the plumbing, not the model.
        </p>
        <div className="hero__cta cta-row">
          <Link href="/billing" className="btn btn--primary">
            Start billing
          </Link>
          <Link href="/docs/cursor" className="link-quiet">
            Add to Cursor
          </Link>
        </div>
        <div className="hero__product">
          <span className="hero__product-label">Drop-in · BYOK · local MVP</span>
          <pre className="hero__snippet">{`curl -s http://localhost:8081/v1/chat/completions \\
  -H "Authorization: Bearer sk-at-dev" \\
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'`}</pre>
          <p className="hero__note">
            OpenAI-compatible · keys <code>sk-at-…</code> · BYOK header{" "}
            <code>X-Ohm-Upstream-Key</code> ·{" "}
            <Link href="/design-partners">Partners</Link> ·{" "}
            <Link href="/docs/terms">Terms</Link> ·{" "}
            <Link href="/docs/pricing">Pricing</Link>
          </p>
        </div>
      </section>

      <section className="social-proof" aria-label="Design partner proof">
        <h2 className="social-proof__title">From the wedge</h2>
        <p className="social-proof__lede">
          Design partners trade measured wait/miss-ratio relief and web-context
          attach rate for a homepage quote.
        </p>
        <ul className="social-proof__list">
          {QUOTES.map((q) => (
            <li key={q.attribution}>
              <blockquote className="social-proof__quote">
                <p>{q.quote}</p>
                <footer>{q.attribution}</footer>
              </blockquote>
            </li>
          ))}
        </ul>
        <p className="social-proof__cta">
          <Link href="/design-partners">Become a design partner</Link>
        </p>
      </section>
    </>
  );
}
