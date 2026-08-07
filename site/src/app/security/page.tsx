import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security",
  description:
    "withOhm security — identical-request-replay cache purpose, hashed keys, account profiles, and compliance links.",
};

export default function SecurityMarketingPage() {
  return (
    <div className="marketing-article">
      <header className="page-head">
        <p className="marketing-article__eyebrow">Resources</p>
        <h1>Security</h1>
        <p>
          withOhm sits between your apps and upstream model providers. Exact-replay
          inventory is purpose-bound. Governance stays on the Pipeline System.
        </p>
        <div className="cta-row marketing-article__cta">
          <Link href="/docs/security" className="btn btn--primary">
            Security docs
          </Link>
          <Link href="/product/waste-demo" className="link-quiet">
            Waste demo
          </Link>
          <Link href="/product" className="link-quiet">
            Product
          </Link>
        </div>
      </header>

      <div className="marketing-article__body prose">
        <h2>Cache purpose</h2>
        <p>
          Identical chat completions may be stored per tenant for replay only.
          Purpose header:{" "}
          <code>X-AT-Cache-Purpose: identical-request-replay</code>. Opt out with{" "}
          <code>cache_control: &quot;no_store&quot;</code>. Replay inventory is{" "}
          <strong>not</strong> a training corpus.
        </p>

        <h2>Keys & tenancy</h2>
        <p>
          Customer API keys are stored hashed (SHA-256) at rest. Suspended
          tenants receive HTTP 403. Issued prefix today is <code>sk-at-…</code>{" "}
          (withOhm brand; rename deferred).
        </p>

        <h2>Receipts & honesty</h2>
        <p>
          Cache HITs can carry a signed <code>X-Ohm-Receipt</code> (Ed25519)
          verifiable against the public JWKS directory. Non-goals are published
          at <code>GET /v1/public/honesty</code> so marketing cannot outrun the
          pipe.
        </p>

        <h2>Subprocessors</h2>
        <p>
          Model providers you enable, AWS (host), Stripe (billing), Amplify
          (marketing site). Details and legal:{" "}
          <Link href="/docs/legal">Legal & compliance</Link>,{" "}
          <Link href="/docs/dpa">DPA</Link>,{" "}
          <Link href="/docs/privacy">Privacy</Link>.
        </p>

        <h2>Report an issue</h2>
        <p>
          Operational questions: <Link href="/support">Support</Link>. Enterprise
          security review or BAA-style conversations:{" "}
          <Link href="/contact">Contact</Link>.
        </p>
      </div>

      <p className="marketing-article__back">
        <Link href="/resources">All resources →</Link>
      </p>
    </div>
  );
}
