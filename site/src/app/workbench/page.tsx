import type { Metadata } from "next";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "Agent Shell",
  description:
    "Ohm Agent Shell — thin workbench that routes chat and tools only through the withOhm pipe.",
};

export default function WorkbenchPage() {
  return (
    <>
      <header className="page-head">
        <h1>Ohm Agent Shell</h1>
        <p>
          A thin workbench that talks only to the withOhm pipe. No Cursor
          required — paste an Intermediate key and use{" "}
          <strong>Run miss→HIT demo</strong> for a one-click proof (model{" "}
          <code>mock</code>). Guided steps also live on{" "}
          <a href="/demo">/demo</a>.
        </p>
      </header>
      <AgentShellClient />
    </>
  );
}
