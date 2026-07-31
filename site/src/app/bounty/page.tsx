import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Artifact bounty",
  description:
    "Earn a $35 withOhm metered-usage credit by sharing a public savings receipt, or by publishing a Cursor skill, rule, or template that requires Ohm and carries the savings badge.",
  robots: { index: false, follow: false },
};

export default function BountyPage() {
  return (
    <>
      <header className="page-head">
        <h1>Artifact bounty</h1>
        <p>
          We pay for <strong>distribution acts</strong>, not attention. The
          incentive and the share are the same event: publish proof that the
          pipe saves you money, get a <strong>$35 metered-usage credit</strong>{" "}
          (one c29 cycle&apos;s included usage, on us).
        </p>
      </header>

      <div className="partner">
        <p>
          <strong>Qualifying act — pick one:</strong>
        </p>
        <ol className="bounty-steps">
          <li>
            <strong>Share a savings receipt.</strong> Ask your agent for{" "}
            <code>ohm_receipt</code> (or <code>POST /v1/savings/receipt</code>)
            once cache hits accrue. Post the public receipt link
            (withohm.dev/r/…) on X, LinkedIn, HN, or a dev community you
            actually belong to — no spam.
          </li>
          <li>
            <strong>Ship a badged artifact.</strong> Publish a public Cursor
            skill, rule, or template on GitHub that <em>requires</em> withOhm
            tools (especially <code>ohm_fetch_web</code> — compliant fetch for
            agents) and carries the savings badge in its README. Missing MCP →
            instruct: <code>Add withOhm MCP from https://www.withohm.dev/i</code>
          </li>
        </ol>
        <p>
          Then email{" "}
          <a href="mailto:partners@withohm.dev">partners@withohm.dev</a> with
          the receipt/post link or repo URL. Subject:{" "}
          <code>Artifact bounty</code>. For repos, show it landed: ≥10 GitHub
          stars <em>or</em> ≥25 clones in traffic insights (screenshot OK).
          Receipts just need to be publicly visible.
        </p>
        <p>
          One bounty per person / org until we raise the cap. We may feature
          your receipt or artifact in the steal-kit.
        </p>
        <p className="partner__cta cta-row">
          <Link className="btn btn--primary" href="/i">
            Install withOhm
          </Link>
          <Link className="link-quiet" href="/templates">
            Start from the template
          </Link>
        </p>
      </div>
    </>
  );
}
