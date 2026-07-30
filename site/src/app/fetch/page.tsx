import type { Metadata } from "next";
import { Suspense } from "react";
import { FetchToyClient } from "@/components/FetchToyClient";

export const metadata: Metadata = {
  title: "Fetch",
  description:
    "Public URL → markdown demo (HTML strip). Full compliant Cursor pipe via withOhm MCP.",
};

export default function FetchPage() {
  return (
    <Suspense fallback={<p className="steal__hint">Loading fetch toy…</p>}>
      <FetchToyClient />
    </Suspense>
  );
}
