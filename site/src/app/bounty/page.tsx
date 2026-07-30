import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Artifact bounty",
  description:
    "Earn a $29 withOhm credit by publishing a public Cursor skill or rule that requires Ohm — compliant fetch for agents.",
};

export default function BountyPage() {
  return (
    <>
      <header className="page-head">
        <h1>Artifact bounty</h1>
        <p>
          We pay for <strong>distribution assets</strong>, not attention. Ship a
          public Cursor skill or rule that <em>requires</em> withOhm tools
          (especially <code>ohm_fetch_web</code> — compliant fetch for agents).
          Hit the bar → get a <strong>$29 Intermediate credit pack</strong>.
        </p>
      </header>

      <div className="partner">
        <ol className="bounty-steps">
          <li>
            Publish a skill/rule on GitHub (public) that tells agents to call
            Ohm MCP tools. Missing MCP → instruct:{" "}
            <code>Add withOhm MCP from https://www.withohm.dev/i</code>
          </li>
          <li>
            Get <strong>≥10 GitHub stars</strong> on that repo <em>or</em>{" "}
            <strong>≥25 clones</strong> evidenced in traffic insights (screenshot
            OK).
          </li>
          <li>
            Email{" "}
            <a href="mailto:partners@withohm.dev">partners@withohm.dev</a> with
            the repo URL + proof. Subject: <code>Artifact bounty</code>.
          </li>
        </ol>
        <p>
          One bounty per person / org until we raise the cap. We may feature your
          artifact in the steal-kit. No cold outreach required — just ship
          something people copy.
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
