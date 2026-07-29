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
          For those who seek long-term partnerships with us, we offer the
          Enterprise subscription: everything in the Intermediate package, plus
          metered transactional usage fees agreed at fixed prices for
          unlimited or budgeted monthly rates (cache hits, cache misses, and URL
          fetches). The extra bonus is design-partner rank — a special standing
          that lets you negotiate a fixed contract for transaction usage. This
          option is designed for large-scale operations that engage in heavy
          scraping daily and on a regular basis. Transaction usage agreements
          offer long-term, substantial discounts on transaction costs through
          fixed monthly prices for cache hits, cache misses, and web fetches —
          treat them as the modern SMS / call-minutes / data model: unlimited-feel
          usage for a salaried fee. Unlimited usage is the main feature of the
          subscription. Alongside that, Enterprise offers live stats emailed
          weekly detailing dedicated usage budgets and utilisation — so you see
          the benefit of fixed-cost agreements in near real time — personal admin
          contact, and an invite to the design-partner forum where clients
          converse directly with withOhm engineers about usage and data
          processing. The ultimate client experience and the most efficient AI
          software-builder workflow, with us at withOhm.
        </p>
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
