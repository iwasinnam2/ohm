import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

const QUOTES = [
  {
    quote:
      "Change one base URL (or one Cursor attach). Keep your keys and SDKs. Gain prompt replay, a clearer pipe, compliant web context — and a bill that rents the plumbing, not the model.",
    attribution: "withOhm — the product promise",
  },
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero__lockup">
          <OhmMark className="hero__mark" />
          <h1 className="hero__brand">withOhm</h1>
        </div>
        <p className="hero__promise">
          Change one base URL (or one Cursor attach). Keep your keys and SDKs.
          Gain prompt replay, a clearer pipe, compliant web context — and a bill
          that rents the plumbing, not the model.
        </p>
        <div className="hero__cta cta-row">
          <Link href="/subscriptions" className="btn btn--primary">
            Explore Subscription
          </Link>
          <Link href="/docs/cursor" className="link-quiet">
            Add to Cursor
          </Link>
        </div>
        <div className="hero__product">
          <span className="hero__product-label">
            Drop-in · BYOK · OpenAI-compatible
          </span>
          <pre className="hero__snippet">{`curl -s http://localhost:8081/v1/chat/completions \\
  -H "Authorization: Bearer sk-at-dev" \\
  -H "X-Ohm-Upstream-Key: $OPENAI_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'`}</pre>
          <p className="hero__note">
            OpenAI-compatible · keys <code>sk-at-…</code> · BYOK header{" "}
            <code>X-Ohm-Upstream-Key</code> ·{" "}
            <Link href="/">Home</Link> ·{" "}
            <Link href="/docs/terms">Terms</Link> ·{" "}
            <Link href="/docs/pricing">Pricing</Link>
          </p>
        </div>
      </section>

      <section className="social-proof" aria-label="Product promise">
        <h2 className="social-proof__title">Built for the pipe</h2>
        <p className="social-proof__lede">
          One attach. Measured relief on wait and miss-ratio. Compliant web
          context without a second stack.
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
          <Link href="/subscriptions">Explore Subscription</Link>
        </p>
      </section>
    </>
  );
}
