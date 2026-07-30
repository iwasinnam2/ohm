import type { Metadata } from "next";
import Link from "next/link";
import { EnterpriseApplicationForm } from "@/components/EnterpriseApplicationForm";

export const metadata: Metadata = {
  title: "Enterprise at withOhm",
  description:
    "Enterprise at withOhm — design-partner rank, negotiated transaction usage agreements, and personal admin contact.",
};

export default function EnterpriseBillingPage() {
  return (
    <>
      <header className="page-head">
        <h1>Enterprise at withOhm</h1>
        <p>
          Everything in Intermediate, plus fixed-price transaction bundles for
          cache hits, cache misses, and web fetches — the modern SMS / minutes /
          data model: unlimited-feel usage for a salaried fee, from{" "}
          <strong>$2,500/month</strong>. Built for large-scale operations with
          heavy daily scraping.
        </p>
        <ul className="tier__pros">
          <li>Negotiated fixed monthly bundles with substantial volume discounts</li>
          <li>Weekly live stats: dedicated usage budgets and utilisation</li>
          <li>Personal admin contact and design-partner forum access</li>
          <li>Managed provider key pools and single-tenant options</li>
        </ul>
      </header>
      <EnterpriseApplicationForm />
      <p className="billing-form__alt">
        Prefer self-serve?{" "}
        <Link href="/billing/intermediate">Intermediate at withOhm</Link>
        {" · "}
        <Link href="/subscriptions">All subscriptions</Link>
      </p>
    </>
  );
}
