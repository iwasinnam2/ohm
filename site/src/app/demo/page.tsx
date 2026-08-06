import type { Metadata } from "next";
import Link from "next/link";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "Agent Shell demo",
  description:
    "Try the withOhm Agent Shell — PowerShell CLI for MCP skills on the pipe.",
};

export default function DemoPage() {
  return (
    <>
      <header className="page-head">
        <h1>Agent Shell — try the pipe</h1>
        <p>
          Same PowerShell CLI as the{" "}
          <Link href="/workbench">Agent Shell</Link>. Path defaults to{" "}
          <code>self-proof</code> for this demo session.
        </p>
        <ol className="demo-steps">
          <li>
            Paste your key:{" "}
            <code>Set-OhmKey -Key sk-at-…</code> (from{" "}
            <Link href="/keys">API keys</Link> or{" "}
            <Link href="/billing/intermediate">Intermediate</Link>).
          </li>
          <li>
            Chat on the pipe:{" "}
            <code>Invoke-OhmChat -Prompt &quot;ohm-self-proof-v1&quot;</code>{" "}
            — run it twice and read the <code>[MISS]</code> / <code>[HIT]</code>{" "}
            prefix.
          </li>
          <li>
            Inspect meters: <code>Get-OhmUsage</code> ·{" "}
            <code>Get-OhmSaving</code> · <code>New-OhmReceipt</code>
          </li>
          <li>
            List MCP skills: <code>Get-OhmSkill</code> · full help:{" "}
            <code>Get-Help</code>
          </li>
        </ol>
      </header>
      <AgentShellClient variant="demo" />
      <p className="receipt__foot">
        <Link href="/workbench">Agent Shell</Link>
        {" · "}
        <Link href="/docs/cursor">MCP skills</Link>
        {" · "}
        <Link href="/org">Analytics</Link>
      </p>
    </>
  );
}
