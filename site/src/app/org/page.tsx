import type { Metadata } from "next";
import Link from "next/link";
import { OrgConsoleClient } from "@/components/OrgConsoleClient";

export const metadata: Metadata = {
  title: "Analytics",
  description:
    "withOhm analytics — live usage tallies, plan configuration, hit-ratio breakdown, and FinOps export.",
};

export default function OrgPage() {
  return (
    <>
      <header className="page-head">
        <h1>Analytics</h1>
        <p>
          Live pipe meters for your seat: plan configuration, usage tallies,
          hit-ratio by path or cost center, and estimated savings. Org setup and
          CSV export live under the fold.{" "}
          <Link href="/keys">API keys</Link>
          {" · "}
          <Link href="/subscriptions">Subscriptions</Link>
          {" · "}
          <Link href="/workbench">Agent Shell</Link>
        </p>
      </header>
      <OrgConsoleClient />
    </>
  );
}
