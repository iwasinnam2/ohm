import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Design partners",
  description:
    "Ten teams. One base_url swap. Quote and miss-ratio improvement for a time-boxed design-partner key.",
};

export default function DesignPartnersPage() {
  return (
    <>
      <header className="page-head">
        <h1>Design partners</h1>
        <p>
          Ten teams with painful rate limits or duplicate cache middleware.
          Time-boxed complimentary key. One public quote. Measured miss-ratio
          improvement.
        </p>
      </header>
      <div className="partner">
        <ol className="partner__steps">
          <li>
            Email{" "}
            <a href="mailto:partners@withohm.dev?subject=Ohm%20design%20partner">
              partners@withohm.dev
            </a>{" "}
            — we issue a <code>design_partner</code> key (legacy prefix{" "}
            <code>sk-at-…</code>; ~90 days + soft quota).
          </li>
          <li>
            You set <code>base_url</code> to the local edge{" "}
            <code>http://localhost:8081/v1</code> (or your operator deploy) and
            your <code>api_key</code> — nothing else. Public{" "}
            <code>api.withohm.dev</code> after AWS cutover.
          </li>
          <li>
            After one week, export <code>cache_hit_ratio</code>,{" "}
            <code>fetches</code>, <code>web_context_attach_rate</code>, and{" "}
            <code>requests</code> from <code>GET /v1/usage</code>.
          </li>
          <li>
            BYOK: send provider key as <code>X-Ohm-Upstream-Key</code>. Optional:{" "}
            <Link href="/docs/cursor">Add Ohm to Cursor</Link>.
          </li>
          <li>
            Accept{" "}
            <Link href="/docs/terms">Terms</Link> /{" "}
            <Link href="/docs/dpa">DPA</Link> for web context; we put your quote
            on the Ohm homepage.
          </li>
        </ol>
        <p className="partner__success">
          Operators: <code>POST /v1/admin/tenants</code> with{" "}
          <code>plan=design_partner</code>, <code>terms_ack</code>,{" "}
          <code>dpa_ack</code>. Partners do not need admin access.
        </p>
        <div className="partner__cta cta-row">
          <a
            className="btn btn--primary"
            href="mailto:partners@withohm.dev?subject=Ohm%20design%20partner"
          >
            Request a key
          </a>
          <Link href="/docs/quickstart" className="link-quiet">
            Read the quickstart
          </Link>
        </div>
      </div>
    </>
  );
}
