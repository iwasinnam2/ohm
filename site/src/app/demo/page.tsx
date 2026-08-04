import type { Metadata } from "next";
import Link from "next/link";
import { AgentShellClient } from "@/components/AgentShellClient";

export const metadata: Metadata = {
  title: "Hit ratio demo",
  description:
    "Identical prompt twice through withOhm — watch MISS become HIT. Hit ratio is the inventory; the spread is the arbitrage.",
};

export default function DemoPage() {
  return (
    <>
      <header className="page-head">
        <h1>Hit ratio in sixty seconds</h1>
        <p>
          Same prompt, twice, through the Ohm pipe. First call misses the
          cache; the second hits. That ratio — how often identical traffic
          replays — is what withOhm meters.
        </p>
        <ol className="demo-steps">
          <li>
            Paste your <code>sk-at-…</code> key (from{" "}
            <Link href="/keys">API keys</Link> or{" "}
            <Link href="/billing/intermediate">Intermediate</Link>).
          </li>
          <li>
            Leave model as <code>mock</code> — no provider key needed for this
            proof. Path defaults to <code>self-proof</code> (feeds hit-ratio).
          </li>
          <li>
            Click <strong>Prove miss → HIT</strong>. Read the strip: first
            MISS, second HIT.
          </li>
          <li>
            Click <strong>Mint public receipt</strong> — shareable{" "}
            <code>/r/…</code> link + README badge (same as{" "}
            <code>POST /v1/savings/receipt</code> / MCP <code>ohm_receipt</code>
            ).
          </li>
        </ol>
      </header>
      <AgentShellClient variant="demo" />
      <p className="receipt__foot">
        <Link href="/workbench">Agent Shell</Link>
        {" · "}
        <Link href="/org">Org ledger</Link>
        {" · "}
        <Link href="/docs/enterprise-chaos">Enterprise chaos</Link>
      </p>
    </>
  );
}
