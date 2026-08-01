import type { Metadata } from "next";
import Link from "next/link";
import { EnterpriseApplicationForm } from "@/components/EnterpriseApplicationForm";

export const metadata: Metadata = {
  title: "Enterprise at withOhm",
  description:
    "Enterprise chaos governor — SSO, clean ledger, org policy, Agent Shell, managed keys from $2,500/month.",
};

export default function EnterpriseBillingPage() {
  return (
    <>
      <header className="page-head">
        <h1>Enterprise at withOhm</h1>
        <p>
          The control plane for enterprise AI chaos: SSO tenancy, cost-center
          ledger, compliance policy, audit logs, and the Ohm Agent Shell —
          from <strong>$2,500/month</strong>. Cursor optional. Govern the
          entropy; rent the plumbing.
        </p>
        <ul className="tier__pros">
          <li>OIDC SSO + SCIM user provisioning</li>
          <li>Corporate clean ledger with FinOps CSV/JSON export</li>
          <li>Org policy: model allowlist, fetch purposes, managed keys</li>
          <li>Audit log of API access and policy denials</li>
          <li>Agent Shell workbench — no IDE lock-in</li>
        </ul>
        <p className="cta-row">
          <Link className="btn" href="/org">
            Org console
          </Link>
          <Link className="btn" href="/workbench">
            Agent Shell
          </Link>
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
