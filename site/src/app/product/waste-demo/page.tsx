import type { Metadata } from "next";
import Link from "next/link";
import { WasteCheckClient } from "@/components/WasteCheckClient";

export const metadata: Metadata = {
  title: "Waste demo — miss → HIT",
  description:
    "Identical agent call twice — first MISS (paid), second HIT (replay, no upstream tokens). withOhm pipe rent on both crossings.",
};

export default function WasteDemoProductPage() {
  return (
    <>
      <header className="page-head">
        <p className="product-hero__eyebrow">Product · Proof</p>
        <h1>Waste demo</h1>
        <p>
          Your agent asked the same thing twice. Bare routing billed the lab
          twice. withOhm answers the second from cache —{" "}
          <strong>no upstream tokens on the HIT</strong> — and still meters pipe
          rent on both crossings.
        </p>
        <ul className="page-head__list">
          <li>Retries and identical prompts stop re-buying the model.</li>
          <li>BYOK — your OpenAI / Anthropic keys stay yours.</li>
          <li>
            Create an account, then attach in Cursor (
            <Link href="/i">/i</Link>).
          </li>
        </ul>
      </header>

      <WasteCheckClient />

      <p className="receipt__foot">
        <Link href="/product">What is withOhm</Link>
        {" · "}
        <Link href="/signup">Create Account</Link>
        {" · "}
        <Link href="/i">Attach in Cursor</Link>
        {" · "}
        <Link href="/workbench">Agent Shell</Link>
      </p>
    </>
  );
}
