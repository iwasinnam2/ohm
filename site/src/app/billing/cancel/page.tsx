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
          once payment fails — start again when ready. Your email and
          organisation are still filled in on the checkout page.
        </p>
      </header>
      <div className="cta-row">
        <Link href="/billing/intermediate" className="btn btn--primary">
          Resume checkout
        </Link>
        <Link href="/subscriptions" className="link-quiet">
          Subscriptions
        </Link>
        <Link href="/support" className="link-quiet">
          Something went wrong? Support
        </Link>
      </div>
    </>
  );
}
