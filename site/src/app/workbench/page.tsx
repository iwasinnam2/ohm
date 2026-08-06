import type { Metadata } from "next";
import Link from "next/link";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "Agent Shell",
  description:
    "withOhm Agent Shell — PowerShell-compatible CLI for MCP skills and the Ohm pipe.",
};

export default function WorkbenchPage() {
  return (
    <>
      <header className="page-head">
        <h1>Ohm Agent Shell</h1>
        <p>
          A PowerShell-style CLI on the withOhm pipe. Authenticate with{" "}
          <code>Set-OhmKey</code>, then run MCP skill cmdlets —{" "}
          <code>Invoke-OhmChat</code>, <code>Get-OhmUsage</code>,{" "}
          <code>Invoke-OhmFetch</code>, and the rest. Same tools as{" "}
          <code>pip install withohm-mcp</code>.{" "}
          <Link href="/docs/cursor">Cursor / MCP docs</Link>
          {" · "}
          <Link href="/keys">API keys</Link>
        </p>
      </header>
      <AgentShellClient variant="workbench" />
    </>
  );
}
