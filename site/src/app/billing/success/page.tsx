"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";
import { persistKey, readStoredKey } from "@/lib/keyStorage";

export default function BillingSuccessPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [upstreamKey, setUpstreamKey] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const key = readStoredKey();
    setApiKey(key);
    if (key) persistKey(key);
  }, []);

  const installHref = useMemo(() => {
    if (!apiKey) return null;
    return cursorOhmInstallHref({
      apiKey,
      upstreamKey: upstreamKey.trim() || undefined,
    });
  }, [apiKey, upstreamKey]);

  async function copyKey() {
    if (!apiKey) return;
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      /* ignore */
    }
  }

  return (
    <section className="postpay">
      <div className="postpay__brand">
        <OhmMark className="postpay__mark" />
        <p className="postpay__eyebrow">Seat active</p>
      </div>

      <h1 className="postpay__title">Your withOhm key</h1>
      <p className="postpay__lede">
        Copy it now if you haven&apos;t already. Prove the pipe in Agent Shell,
        or wire Cursor from the integrations board.
      </p>

      {apiKey ? (
        <div className="billing-form__key-panel postpay__key-hero">
          <code className="billing-form__key-code">{apiKey}</code>
          <button type="button" className="btn btn--primary" onClick={copyKey}>
            {copied ? "Copied" : "Copy key"}
          </button>
        </div>
      ) : (
        <p className="billing-form__error" role="alert">
          Key not found in this browser. Restore it on{" "}
          <Link href="/keys">API keys</Link>, or mint a new one at{" "}
          <Link href="/billing/intermediate">Intermediate checkout</Link>.
        </p>
      )}

      <div className="cta-row postpay__next">
        <Link href="/demo" className="btn btn--primary">
          Run hit ratio demo
        </Link>
        <Link href="/workbench" className="btn">
          Open Agent Shell
        </Link>
      </div>

      {installHref ? (
        <details className="postpay__key">
          <summary>Optional — add MCP to Cursor</summary>
          <label className="postpay__upstream">
            <span>Provider key for BYOK (optional)</span>
            <input
              type="password"
              autoComplete="off"
              placeholder="sk-… or Anthropic key"
              value={upstreamKey}
              onChange={(e) => setUpstreamKey(e.target.value)}
            />
          </label>
          <a className="btn postpay__cta" href={installHref}>
            Add withOhm to Cursor
          </a>
          <p className="postpay__cta-note">
            Compatibility client — not required to use withOhm.
          </p>
        </details>
      ) : null}

      <p className="postpay__cta-note">
        Once cache hits accrue, mint a public receipt via{" "}
        <code>ohm_receipt</code> or the API — see{" "}
        <Link href="/docs/quickstart">Quickstart</Link>. Sharing one qualifies
        for the <Link href="/bounty">$35 artifact bounty</Link>.
      </p>

      <p className="postpay__cta-note">
        <Link href="/org">Org console</Link>
        {" · "}
        <Link href="/docs/pricing">Metered rates</Link>
        {" · "}
        <Link href="/i">Install path</Link>
      </p>
    </section>
  );
}
