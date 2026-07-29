import type { Metadata } from "next";
import Link from "next/link";
import { DesignPartnerApplicationForm } from "@/components/DesignPartnerApplicationForm";

export const metadata: Metadata = {
  title: "Founding design partners",
  description:
    "Apply for a complimentary 90-day withOhm design-partner seat — Cursor MCP, BYOK, solo builders welcome.",
};

export default function DesignPartnersPage() {
  return (
    <>
      <header className="page-head">
        <h1>Founding design partners</h1>
        <p>
          Looking for ~10 Cursor power users (solo is fine) who hit rate limits,
          re-run the same prompts, or need compliant web context in agents.
          Complimentary <strong>90-day</strong> seat in exchange for one public
          quote and a short <code>/v1/usage</code> before/after.
        </p>
        <p>
          No warm intro required — apply below, or start the{" "}
          <Link href="/billing/intermediate">Intermediate trial</Link> today and
          attach via <strong>Add withOhm to Cursor</strong> after Checkout.
        </p>
      </header>

      <div className="partner">
        <DesignPartnerApplicationForm />
        <p className="partner__cta cta-row">
          <Link href="/docs/cursor" className="link-quiet">
            Cursor / MCP docs
          </Link>
          <Link href="/subscriptions" className="link-quiet">
            All plans
          </Link>
        </p>
      </div>
    </>
  );
}
