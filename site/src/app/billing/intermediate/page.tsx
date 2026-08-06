import type { Metadata } from "next";
import Link from "next/link";
import { BillingCheckoutForm } from "@/components/BillingCheckoutForm";
import { PAYG_RATES, COMMIT_TIERS, formatUsd, formatUsdMoney } from "@/lib/meterRates";

export const metadata: Metadata = {
  title: "Intermediate at withOhm",
  description:
    "Intermediate at withOhm — usage-led pipe rent with $0 membership and metered cache + web fetch, or a monthly commit tier with included usage.",
};

const INTERMEDIATE_PROS = [
  "Cursor integration — one-click MCP attach",
  "URL search and web context on the pipe",
  "Bring your own provider keys (BYOK)",
  "Real-time model switching with zero local resource drag",
  "Centralised prompt cache and compliant search",
];

export default async function IntermediateBillingPage({
  searchParams,
}: {
  searchParams: Promise<{ commit?: string }>;
}) {
  const params = await searchParams;
  const commit =
    COMMIT_TIERS.find((t) => t.id === (params.commit || "").toLowerCase()) ??
    null;
  return (
    <>
      <header className="page-head">
        <h1>Intermediate at withOhm</h1>
        <p>Intermediate at withOhm is the flagship service we offer:</p>
        <ul className="page-head__list">
          {INTERMEDIATE_PROS.map((pro) => (
            <li key={pro}>{pro}</li>
          ))}
        </ul>
        {commit ? (
          <p>
            <strong>
              {formatUsdMoney(commit.usd_month)}/mo commit —{" "}
              {formatUsdMoney(commit.included_usd)} metered usage included each
              cycle.
            </strong>{" "}
            Model tokens stay on your provider keys (BYOK). Checkout issues your
            withOhm API key once.
          </p>
        ) : (
          <p>
            <strong>$0 membership</strong> with card on file. Prefer a fixed
            monthly line? <Link href="/subscriptions">Pick a commit tier</Link>.
            Model tokens stay on your provider keys (BYOK). Checkout issues your
            withOhm API key once.
          </p>
        )}
      </header>
      <BillingCheckoutForm commit={commit?.id ?? ""} />
      <section className="billing-meter-fineprint" aria-label="Meter rates">
        <p>
          Usage meters invoice monthly after you use the pipe — they are not
          checkout line items. List rates: cache hit{" "}
          {formatUsd(PAYG_RATES.cache_hit)}/1k tokens · cache miss{" "}
          {formatUsd(PAYG_RATES.cache_miss)}/1k tokens · web fetch{" "}
          {formatUsd(PAYG_RATES.web_fetch)}/URL.
          {commit
            ? " Overage beyond the included commit bills at these rates."
            : null}{" "}
          <Link href="/docs/pricing">Full pricing</Link>.
        </p>
      </section>
      <p className="billing-form__alt">
        Need fixed usage agreements?{" "}
        <Link href="/billing/enterprise">Enterprise at withOhm</Link>
        {" · "}
        <Link href="/docs/pricing">Meter rates</Link>
        {" · "}
        <Link href="/subscriptions">All subscriptions</Link>
      </p>
    </>
  );
}
