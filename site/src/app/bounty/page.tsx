import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Artifact bounty",
  description:
    "Earn a $35 withOhm metered-usage credit by sharing a public savings receipt from the waste check, or by publishing a Cursor skill that requires Ohm.",
};

export default function BountyPage() {
  return (
    <>
      <header className="page-head">
        <h1>Artifact bounty</h1>
        <p>
          We pay for <strong>distribution acts</strong>, not attention. The
          incentive and the share are the same event: publish proof that the
          pipe stops re-buying identical calls, get a{" "}
          <strong>$35 metered-usage credit</strong> (one c29 cycle&apos;s
          included usage, on us).
        </p>
      </header>

      <div className="partner">
        <p>
          <strong>Qualifying act — pick one:</strong>
        </p>
        <ol className="bounty-steps">
          <li>
            <strong>Share a savings receipt.</strong> Run the{" "}
            <Link href="/demo">waste check</Link> (MISS → HIT), mint a public
            receipt under <em>your</em> $0 seat key, then post the{" "}
            <code>withohm.dev/r/…</code> link on X, LinkedIn, HN, or a community
            you belong to — no spam. (MCP path: <code>ohm_receipt</code> /{" "}
            <code>POST /v1/savings/receipt</code> after cache hits accrue.)
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
          <Link className="btn btn--primary" href="/demo">
            Run the waste check
          </Link>
          <Link className="link-quiet" href="/i">
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
