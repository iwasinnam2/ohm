import type { Metadata } from "next";
import Link from "next/link";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "Agent Shell",
  description:
    "Ohm Agent Shell — thin workbench that routes chat only through the withOhm pipe.",
};

export default function WorkbenchPage() {
  return (
    <>
      <header className="page-head">
        <h1>Ohm Agent Shell</h1>
        <p>
          A thin workbench on the withOhm pipe. Paste your key and chat — or
          run the one-click{" "}
          <Link href="/demo">hit ratio demo</Link> with model{" "}
          <code>mock</code>.
        </p>
      </header>
      <AgentShellClient variant="workbench" />
    </>
  );
}
