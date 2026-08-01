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
          required — bring any OpenAI-compatible key bound to your org.
        </p>
      </header>
      <AgentShellClient />
    </>
  );
}
