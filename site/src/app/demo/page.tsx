import type { Metadata } from "next";
import Link from "next/link";
import { WasteCheckClient } from "@/components/WasteCheckClient";

export const metadata: Metadata = {
  title: "Waste check — miss → HIT",
  description:
    "Hit your Cursor limit mid-month? Watch why: identical agent call twice — first MISS (paid), second HIT (replay, no upstream tokens).",
};

export default function DemoPage() {
  return (
    <>
      <header className="page-head">
        <h1>Hit your Cursor limit mid-month? Watch why.</h1>
        <p>
          Your agent asked the same thing twice. The IDE billed you twice.
          withOhm answers the second from cache —{" "}
          <strong>no upstream tokens on the HIT</strong>.
        </p>
        <p>
          Identical agent call twice: first <code>MISS</code> (paid), second{" "}
          <code>HIT</code> (replay). Mock proves the mechanics; your real models
          work the same through the pipe.
        </p>
        <ul className="page-head__list">
          <li>
            Retries, research loops, and identical prompts stop re-buying the
            model.
          </li>
          <li>BYOK — your OpenAI / Anthropic keys stay yours.</li>
          <li>
            $0 Intermediate seat + MCP attach in two minutes (
            <Link href="/i">/i</Link>).
          </li>
        </ul>
      </header>

      <WasteCheckClient />

      <p className="receipt__foot">
        <Link href="/i">Attach in Cursor</Link>
        {" · "}
        <Link href="/bounty">$100 artifact bounty</Link>
        {" · "}
        <Link href="/billing/intermediate">$0 seat</Link>
        {" · "}
        <Link href="/workbench">Agent Shell</Link>
        {" · "}
        <Link href="/use-cases/enterprise-chaos">Enterprise / team chaos</Link>
      </p>
    </>
  );
}
