import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";

const QUOTES = [
  {
    quote:
      "Compliant fetch for agents — change one Cursor attach. Keep your keys. Prompt replay, public URL context, pipe rent — not token wholesale.",
    attribution: "withOhm — the product promise",
  },
];

const SHARE_LINE = "Add withOhm MCP from https://www.withohm.dev/i";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero__lockup">
          <OhmMark className="hero__mark" />
          <h1 className="hero__brand">withOhm</h1>
        </div>
        <p className="hero__promise">
          <strong>Compliant fetch for agents.</strong> One Cursor attach. Keep
          your keys and SDKs. Prompt replay, public URL context, and a bill that
          rents the plumbing — not the model.
        </p>
        <div className="hero__cta cta-row">
          <Link href="/i" className="btn btn--primary">
            Install /i
          </Link>
          <Link href="/fetch" className="link-quiet">
            Try fetch toy
          </Link>
          <Link href="/templates" className="link-quiet">
            Steal template
          </Link>
        </div>
        <div className="hero__product">
          <span className="hero__product-label">
            Paste this to a teammate — that is the product
          </span>
          <pre className="hero__snippet">{SHARE_LINE}</pre>
          <p className="hero__note">
            $0 Intermediate membership · BYOK ·{" "}
            <Link href="/subscriptions">Subscriptions</Link> ·{" "}
            <Link href="/bounty">Artifact bounty</Link> ·{" "}
            <Link href="/docs/steal-kit">Steal-kit</Link>
          </p>
        </div>
      </section>

      <section className="social-proof" aria-label="Product promise">
        <h2 className="social-proof__title">Built to be copied</h2>
        <p className="social-proof__lede">
          Templates, meme install URLs, and a public fetch toy. Not a traveling
          salesman loop.
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
          <Link href="/i">{SHARE_LINE}</Link>
        </p>
      </section>
    </>
  );
}
