import type { Metadata } from "next";
import { OhmMark } from "@/components/OhmMark";

export const metadata: Metadata = {
  title: "API edge pending",
  description:
    "api.withohm.dev is reserved for the withOhm gateway. Documentation lives on withohm.dev.",
  robots: { index: false, follow: true },
};

export default function EdgePendingPage() {
  return (
    <section className="hero">
      <div className="hero__lockup">
        <OhmMark className="hero__mark" />
        <h1 className="hero__brand" style={{ fontSize: "clamp(2.5rem, 8vw, 4rem)" }}>
          Edge pending
        </h1>
      </div>
      <p className="hero__promise">
        This host is not serving the withOhm OpenAI-compatible gateway. The
        live API is at <code>api.withohm.dev</code>; documentation lives on
        withohm.dev.
      </p>
      <div className="hero__cta cta-row">
        <a className="btn btn--primary" href="https://www.withohm.dev">
          Go to withohm.dev
        </a>
        <a href="https://www.withohm.dev/docs/quickstart" className="link-quiet">
          Quickstart
        </a>
      </div>
      <div className="hero__product">
        <span className="hero__product-label">Supported contract</span>
        <pre className="hero__snippet">{`# Live API
curl -s https://api.withohm.dev/v1/chat/completions \\
  -H "Authorization: Bearer sk-at-..." \\
  -H "Content-Type: application/json" \\
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'`}</pre>
        <p className="hero__note">
          Keys use legacy <code>sk-at-…</code> · Docs & legal:{" "}
          <a href="https://www.withohm.dev/docs/terms">Terms</a> ·{" "}
          <a href="https://www.withohm.dev/docs/privacy">Privacy</a> ·{" "}
          <a href="https://www.withohm.dev/docs/dpa">DPA</a>
        </p>
      </div>
    </section>
  );
}
