import type { Metadata } from "next";
import { OrgConsoleClient } from "@/components/OrgConsoleClient";

export const metadata: Metadata = {
  title: "Org console",
  description:
    "withOhm org console — cost centers, policy, clean ledger export, SSO session.",
};

export default function OrgPage() {
  return (
    <>
      <header className="page-head">
        <h1>Org console</h1>
        <p>
          Govern AI chaos: cost centers, policy profiles, audit, and FinOps
          export. Humans via SSO session; agents via org-bound API keys.
        </p>
      </header>
      <OrgConsoleClient />
    </>
  );
}
