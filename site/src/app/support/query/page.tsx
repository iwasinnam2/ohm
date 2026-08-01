import type { Metadata } from "next";
import Link from "next/link";
import { SupportQueryForm } from "@/components/SupportQueryForm";

export const metadata: Metadata = {
  title: "Submit a query",
  description:
    "Send a support query to withOhm — billing, metering, setup, or anything the FAQs did not cover.",
};

export default function SupportQueryPage() {
  return (
    <>
      <header className="page-head">
        <h1>Submit a query</h1>
        <p>
          Goes straight to <a href="mailto:queries@withohm.dev">queries@withohm.dev</a>{" "}
          — a human replies to the address you provide. Check the{" "}
          <Link href="/support">FAQs</Link> first if you haven&apos;t.
        </p>
      </header>
      <SupportQueryForm />
    </>
  );
}
