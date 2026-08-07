import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CopyBlock } from "@/components/CopyBlock";
import { OhmMark } from "@/components/OhmMark";
import { formatUsd, getPublicReceipt } from "@/lib/publicApi";

type Props = {
  params: Promise<{ token: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { token } = await params;
  const data = await getPublicReceipt(token);
  if (!data) return { title: "Savings receipt" };
  const { receipt } = data;
  const avoided =
    receipt.estimated_provider_avoided_usd ??
    receipt.estimated_upstream_avoided_usd;
  const saved = formatUsd(avoided);
  return {
    title: `${receipt.display_name} saved ~${saved}`,
    description:
      `${receipt.display_name} avoided an estimated ${saved} of upstream ` +
      "model spend with withOhm prompt replay — identical prompts served " +
      "from cache instead of re-billing the provider.",
    robots: { index: false, follow: true },
  };
}

function shareLinks(data: NonNullable<Awaited<ReturnType<typeof getPublicReceipt>>>) {
  const avoided =
    data.receipt.estimated_provider_avoided_usd ??
    data.receipt.estimated_upstream_avoided_usd;
  const saved = formatUsd(avoided);
  const text = `We avoided ~${saved} of upstream model spend with @withOhm prompt replay. Receipt:`;
  return {
    x: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(data.receipt_url)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(data.receipt_url)}`,
  };
}

export default async function ReceiptPage({ params }: Props) {
  const { token } = await params;
  const data = await getPublicReceipt(token);
  if (!data) notFound();

  const { receipt } = data;
  const avoided =
    receipt.estimated_provider_avoided_usd ??
    receipt.estimated_upstream_avoided_usd;
  const saved = formatUsd(avoided);
  const hitPct = Math.round((receipt.cache_hit_ratio || 0) * 100);
  const roi =
    receipt.roi_ratio != null && Number.isFinite(receipt.roi_ratio)
      ? `${receipt.roi_ratio.toFixed(1)}×`
      : null;
  const minted = new Date(receipt.created_at * 1000).toLocaleDateString(
    "en-US",
    { year: "numeric", month: "short", day: "numeric" }
  );
  const share = shareLinks(data);

  return (
    <section className="receipt">
      <header className="page-head">
        <p className="receipt__eyebrow">
          <OhmMark className="receipt__mark" /> Savings receipt
        </p>
        <h1 className="receipt__headline">
          {receipt.display_name} saved <strong>~{saved}</strong>
        </h1>
        <p>
          Estimated upstream model spend avoided via withOhm prompt replay —
          identical prompts served from Redis instead of re-billing the
          provider. Snapshot minted {minted}. Estimate, not a promise.
        </p>
      </header>

      <dl className="receipt__figures">
        <div className="receipt__figure">
          <dt>Estimated provider avoided</dt>
          <dd>~{saved}</dd>
        </div>
        <div className="receipt__figure">
          <dt>Cache hit ratio</dt>
          <dd>{hitPct}%</dd>
        </div>
        <div className="receipt__figure">
          <dt>Replayed tokens</dt>
          <dd>{Math.round(receipt.cache_hit_tokens).toLocaleString("en-US")}</dd>
        </div>
        {receipt.pipe_rent_usd != null ? (
          <div className="receipt__figure">
            <dt>Pipe rent</dt>
            <dd>{formatUsd(receipt.pipe_rent_usd)}</dd>
          </div>
        ) : null}
        {roi ? (
          <div className="receipt__figure">
            <dt>ROI (est.)</dt>
            <dd>{roi}</dd>
          </div>
        ) : null}
      </dl>

      <div className="receipt__actions cta-row">
        <a
          className="btn btn--primary"
          href={share.x}
          target="_blank"
          rel="noopener noreferrer"
        >
          Share on X
        </a>
        <a
          className="link-quiet"
          href={share.linkedin}
          target="_blank"
          rel="noopener noreferrer"
        >
          Share on LinkedIn
        </a>
        <Link className="link-quiet" href="/bounty">
          Sharing pays — $100 bounty
        </Link>
      </div>

      <div className="receipt__badge">
        <h2>README badge</h2>
        <p>
          Drop this in a repo README — it renders a live shields.io badge
          linking back to this receipt.
        </p>
        <CopyBlock text={data.badge_markdown} label="Badge markdown" compact />
      </div>

      <p className="receipt__foot">
        Want your own receipt? Get a $0 seat at{" "}
        <Link href="/billing/intermediate">Intermediate checkout</Link>, run the{" "}
        <Link href="/demo">waste check</Link>, mint under your name, post it
        publicly (e.g. &quot;My monthly savings simply from choosing
        withOhm&quot;), then email the <em>social post URL</em> for the{" "}
        <Link href="/bounty">$100 bounty</Link>.
      </p>
    </section>
  );
}
