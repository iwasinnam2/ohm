import type { Metadata } from "next";
import Link from "next/link";
import { BillingCheckoutForm } from "@/components/BillingCheckoutForm";

export const metadata: Metadata = {
  title: "Intermediate at withOhm",
  description:
    "Intermediate at withOhm — Cursor integration, URL search, proxy-managed keys, and centralised cache on the pipe.",
};

const INTERMEDIATE_PROS = [
  "Cursor integration — one-click MCP attach",
  "URL search and web context on the pipe",
  "Proxy-managed keys for streamlined upstream access",
  "Real-time model switching with zero local resource drag",
  "Centralised prompt cache and compliant search",
];

export default function IntermediateBillingPage() {
  return (
    <>
      <header className="page-head">
        <h1>Intermediate at withOhm</h1>
        <p>
          Intermediate at withOhm is the flagship service we offer:
        </p>
        <ul className="page-head__list">
          {INTERMEDIATE_PROS.map((pro) => (
            <li key={pro}>{pro}</li>
          ))}
        </ul>
        <p>
          $29 monthly seat. Checkout issues your withOhm API key once; Stripe
          collects the subscription. Model tokens stay on your provider keys
          (BYOK).
        </p>
      </header>
      <BillingCheckoutForm />
      <p className="billing-form__alt">
        Need fixed usage agreements?{" "}
        <Link href="/billing/enterprise">Enterprise at withOhm</Link>
        {" · "}
        <Link href="/subscriptions">All subscriptions</Link>
      </p>
    </>
  );
}
