import type { Metadata } from "next";
import Link from "next/link";
import { BillingCheckoutForm } from "@/components/BillingCheckoutForm";
import { PAYG_RATES, formatUsd } from "@/lib/meterRates";

export const metadata: Metadata = {
  title: "Intermediate at withOhm",
  description:
    "Intermediate at withOhm — usage-led pipe rent with $0 membership and metered cache + web fetch.",
};

const INTERMEDIATE_PROS = [
  "Cursor integration — one-click MCP attach",
  "URL search and web context on the pipe",
  "Bring your own provider keys (BYOK)",
  "Real-time model switching with zero local resource drag",
  "Centralised prompt cache and compliant search",
];

export default function IntermediateBillingPage() {
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
        <p>
          <strong>$0 membership</strong> with card on file. You are billed for
          pipe rent: cache hit {formatUsd(PAYG_RATES.cache_hit)}/1k tokens, cache
          miss {formatUsd(PAYG_RATES.cache_miss)}/1k tokens, web fetch{" "}
          {formatUsd(PAYG_RATES.web_fetch)}/URL. Optional $29 credit pack prepaid
          toward meters. Model tokens stay on your provider keys (BYOK). Checkout
          issues your withOhm API key once.
        </p>
      </header>
      <BillingCheckoutForm />
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
