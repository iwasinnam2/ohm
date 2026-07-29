import type { Metadata } from "next";
import { OhmMark } from "@/components/OhmMark";

export const metadata: Metadata = {
  title: "API edge pending",
  description:
    "api.withohm.dev is reserved for the Ohm gateway. Documentation lives on withohm.dev.",
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
        <code>api.withohm.dev</code> is reserved for the Ohm OpenAI-compatible
        gateway (ACM certificate issued). It is not the documentation site and
        does not serve chat completions yet.
      </p>
      <div className="hero__cta cta-row">
        <a className="btn btn--primary" href="https://withohm.dev">
          Go to withohm.dev
        </a>
        <a href="https://withohm.dev/docs/quickstart" className="link-quiet">
          Quickstart (local :8081)
        </a>
      </div>
      <div className="hero__product">
        <span className="hero__product-label">MVP contract</span>
        <pre className="hero__snippet">{`# Supported today
curl -s http://localhost:8081/v1/chat/completions \\
  -H "Authorization: Bearer sk-at-dev" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"mock","messages":[{"role":"user","content":"hi"}]}'

# This host → HTTP 503 JSON for /v1 and /health until AWS cutover`}</pre>
        <p className="hero__note">
          Keys use legacy <code>sk-at-…</code> · Docs & legal:{" "}
          <a href="https://withohm.dev/docs/terms">Terms</a> ·{" "}
          <a href="https://withohm.dev/docs/privacy">Privacy</a> ·{" "}
          <a href="https://withohm.dev/docs/dpa">DPA</a>
        </p>
      </div>
    </section>
  );
}
