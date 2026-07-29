import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Billing cancelled",
  description: "withOhm Checkout was cancelled.",
  robots: { index: false, follow: false },
};

export default function BillingCancelPage() {
  return (
    <>
      <header className="page-head">
        <h1>Checkout cancelled</h1>
        <p>
          No charge was completed. Your withOhm key (if issued) may be suspended
          once payment fails — start again when ready.
        </p>
      </header>
      <p>
        <Link href="/billing/intermediate">Return to Intermediate</Link> ·{" "}
        <Link href="/subscriptions">Subscriptions</Link>
      </p>
    </>
  );
}
