import type { Metadata } from "next";
import Link from "next/link";
import { BillingCheckoutForm } from "@/components/BillingCheckoutForm";

export const metadata: Metadata = {
  title: "Billing",
  description:
    "Self-serve Ohm seat — pipe access, BYOK model path, metered cache and compliant web fetch.",
};

export default function BillingPage() {
  return (
    <>
      <header className="page-head">
        <h1>Start on the pipe</h1>
        <p>
          Checkout issues your Ohm API key once, then Stripe collects the monthly
          seat. Model tokens stay on your provider keys. Web fetch and cache are
          metered by Ohm.
        </p>
      </header>
      <BillingCheckoutForm />
      <p className="billing-form__alt">
        Prefer complimentary access?{" "}
        <Link href="/design-partners">Design partners</Link>
      </p>
    </>
  );
}
