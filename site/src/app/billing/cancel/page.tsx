import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Billing cancelled",
  description: "Ohm Checkout was cancelled.",
  robots: { index: false, follow: false },
};

export default function BillingCancelPage() {
  return (
    <>
      <header className="page-head">
        <h1>Checkout cancelled</h1>
        <p>
          No charge was completed. Your Ohm key (if issued) may be suspended once
          payment fails — start again when ready.
        </p>
      </header>
      <p>
        <Link href="/billing">Return to billing</Link> ·{" "}
        <Link href="/design-partners">Design partners</Link>
      </p>
    </>
  );
}
