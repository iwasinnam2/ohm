import type { Metadata } from "next";
import Link from "next/link";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "60s miss→HIT demo",
  description:
    "Prove withOhm in sixty seconds — identical call twice, watch Redis HIT and the ledger tick.",
};

export default function DemoPage() {
  return (
    <>
      <header className="page-head">
        <h1>60s miss→HIT demo</h1>
        <p>
          Paste an Intermediate key, leave model as <code>mock</code>, click{" "}
          <strong>Run miss→HIT demo</strong>. First call MISS, second HIT —
          ledger strip updates. No Cursor required.
        </p>
        <ol className="demo-steps">
          <li>
            Restore a key on <Link href="/keys">API keys</Link>, or mint one at{" "}
            <Link href="/billing/intermediate">Intermediate ($0 seat)</Link>.
          </li>
          <li>Paste the key below. Upstream/BYOK optional for <code>mock</code>.</li>
          <li>
            Click <strong>Run miss→HIT demo</strong> — fixed prompt{" "}
            <code>ohm-self-proof-v1</code> twice.
          </li>
          <li>
            Optional: mint a public receipt via API / MCP — see repo{" "}
            <code>docs/SELF_PROOF.md</code>.
          </li>
        </ol>
      </header>
      <AgentShellClient />
      <p className="receipt__foot">
        Full workbench: <Link href="/workbench">/workbench</Link>
        {" · "}
        Org ledger: <Link href="/org">/org</Link>
      </p>
    </>
  );
}
