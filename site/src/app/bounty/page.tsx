import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Artifact bounty — $100",
  description:
    "Earn a $100 withOhm metered-usage credit by posting your savings receipt on social media and emailing the post link. Clear rules — no ambiguous claims.",
};

export default function BountyPage() {
  return (
    <>
      <header className="page-head">
        <h1>Artifact bounty — $100</h1>
        <p>
          We pay for a <strong>public distribution act</strong>, not for
          minting a receipt in private. Publish your withOhm savings receipt on
          social, then email us the <strong>post URL</strong>. You get a{" "}
          <strong>$100 metered-usage credit</strong> on your Intermediate seat.
        </p>
        <p>
          Indie proof path:{" "}
          <Link href="/demo">waste check</Link> → mint → post → claim. Need a
          seat first? <Link href="/signup">Sign up — $0 Intermediate</Link>.
          Teams governing shadow AI: see{" "}
          <Link href="/use-cases/enterprise-chaos">chaos governor</Link>.
        </p>
      </header>

      <div className="partner">
        <h2>What you must send</h2>
        <p>
          Email{" "}
          <a href="mailto:partners@withohm.dev">partners@withohm.dev</a> with
          subject <code>Artifact bounty</code> and <strong>exactly these
          three links</strong>:
        </p>
        <ol className="bounty-steps">
          <li>
            <strong>Your public savings receipt</strong> — a{" "}
            <code>https://www.withohm.dev/r/…</code> URL minted under{" "}
            <em>your</em> seat key (from the{" "}
            <Link href="/demo">waste check</Link> or{" "}
            <code>ohm_receipt</code>).
          </li>
          <li>
            <strong>Your social media post URL</strong> — the live post on X,
            LinkedIn, Reddit, HN, or a public Discord/Forum thread{" "}
            <em>you</em> own, where that receipt is shared. This is what earns
            the bounty. A receipt link alone does <strong>not</strong> qualify.
          </li>
          <li>
            <strong>Your withOhm seat email</strong> (the one on the Intermediate
            checkout) so we can apply the $100 credit to the right tenant.
          </li>
        </ol>

        <h2>How to write the post</h2>
        <p>
          Use a clear headline so the share is unambiguous. Example headers
          (copy and adapt):
        </p>
        <ul className="page-head__list">
          <li>
            <em>My monthly savings simply from choosing withOhm</em>
          </li>
          <li>
            <em>Agent loops were re-buying tokens — here&apos;s my withOhm
            waste-check receipt</em>
          </li>
          <li>
            <em>MISS → HIT: identical prompt twice, second call didn&apos;t
            re-buy the model</em>
          </li>
        </ul>
        <p>
          In the body: one or two sentences on what you ran, then paste the
          full <code>withohm.dev/r/…</code> receipt link. Optional: the README
          badge markdown from the receipt page.
        </p>

        <h2>Qualifies</h2>
        <ul className="page-head__list">
          <li>
            Post is <strong>public</strong> (no login wall, no private account)
            and still live when we check.
          </li>
          <li>
            Post clearly shows <strong>your</strong> receipt URL (not someone
            else&apos;s, not a screenshot-only claim without the link).
          </li>
          <li>
            Receipt was minted after a real miss→HIT (or accrued cache hits) on
            a seat you control.
          </li>
          <li>One bounty per person / org until we raise the cap.</li>
        </ul>

        <h2>Does not qualify</h2>
        <ul className="page-head__list">
          <li>
            Emailing only the <code>/r/…</code> receipt with no social post URL.
          </li>
          <li>
            Private DMs, locked accounts, deleted posts, or “I posted then
            deleted it.”
          </li>
          <li>
            Duplicate claims, shared receipts across multiple people, or spam
            blasts to communities you don&apos;t belong to.
          </li>
          <li>
            Repo-only submissions without a public social/post URL (unless you
            use the alternate path below and meet its bar).
          </li>
        </ul>

        <h2>Alternate path — badged artifact</h2>
        <p>
          Instead of a social receipt post, you may publish a{" "}
          <strong>public GitHub</strong> Cursor skill, rule, or template that{" "}
          <em>requires</em> withOhm (especially <code>ohm_fetch_web</code>) and
          carries the savings badge in the README. Missing MCP → instruct:{" "}
          <code>Add withOhm MCP from https://www.withohm.dev/i</code>. Email the
          repo URL plus proof it landed (≥10 GitHub stars <em>or</em> ≥25 clones
          in traffic insights — screenshot OK). Same $100 credit, same one-per-
          person rule.
        </p>

        <h2>How we decide</h2>
        <p>
          We verify the three links (or the repo bar). If anything is missing or
          private, we reply once asking you to fix it — we do not negotiate
          partial credit. Credit is a <strong>$100 metered-usage grant</strong>{" "}
          on your Intermediate seat (pipe meters), not cash and not a Cursor
          subscription refund. We may feature your receipt or post in the
          steal-kit.
        </p>

        <p className="partner__cta cta-row">
          <Link className="btn btn--primary" href="/demo">
            Run the waste check
          </Link>
          <Link className="link-quiet" href="/i">
            Install withOhm
          </Link>
          <Link className="link-quiet" href="/billing/intermediate">
            $0 seat
          </Link>
        </p>
      </div>
    </>
  );
}
