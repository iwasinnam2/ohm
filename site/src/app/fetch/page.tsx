import type { Metadata } from "next";
import { Suspense } from "react";
import { FetchToyClient } from "@/components/FetchToyClient";

export const metadata: Metadata = {
  title: "Fetch",
  description:
    "Public compliant fetch for agents — paste a URL, get markdown via withOhm.",
};

export default function FetchPage() {
  return (
    <Suspense fallback={<p className="steal__hint">Loading fetch toy…</p>}>
      <FetchToyClient />
    </Suspense>
  );
}
