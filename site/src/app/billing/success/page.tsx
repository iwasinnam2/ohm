"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";

const KEY_STORAGE = "ohm_api_key";

export default function BillingSuccessPage() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [upstreamKey, setUpstreamKey] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    try {
      setApiKey(sessionStorage.getItem(KEY_STORAGE));
    } catch {
      setApiKey(null);
    }
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
      window.setTimeout(() => setCopied(false), 2000);
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

      <h1 className="postpay__title">Feel the difference in Cursor</h1>
      <p className="postpay__lede">
        One click opens Cursor’s MCP installer with your withOhm seat already wired.
        No JSON to paste. Confirm once — then work with cache replay and
        compliant fetch for agents on the pipe.
      </p>

      <div className="postpay__contrast" aria-label="Before and after withOhm">
        <p className="postpay__before">
          <span className="postpay__label">Before</span>
          Waiting on clogged model calls. Hand-browsing the public web for
          agents.
        </p>
        <p className="postpay__after">
          <span className="postpay__label">After</span>
          Prompt replay from Redis. Legal public-web context as an MCP tool —
          in the same Cursor workflow.
        </p>
      </div>

      {installHref ? (
        <div className="postpay__cta-block">
          <label className="postpay__upstream">
            <span>Optional — provider key for BYOK model calls</span>
            <input
              type="password"
              autoComplete="off"
              placeholder="sk-… or Anthropic key (stored only in this Cursor MCP env)"
              value={upstreamKey}
              onChange={(e) => setUpstreamKey(e.target.value)}
            />
          </label>
          <a className="btn btn--primary postpay__cta" href={installHref}>
            Add withOhm to Cursor
          </a>
          <p className="postpay__cta-note">
            Opens Cursor → MCP install confirm. Your withOhm key is already in
            the config.
          </p>
        </div>
      ) : (
        <div className="postpay__cta-block">
          <p className="billing-form__error">
            withOhm key missing from this browser session. Start again from{" "}
            <Link href="/billing/intermediate">Intermediate checkout</Link> so we
            can wire the one-click install.
          </p>
        </div>
      )}

      <details className="postpay__key">
        <summary>Your withOhm API key</summary>
        {apiKey ? (
          <p>
            <code>{apiKey}</code>{" "}
            <button type="button" className="link-quiet" onClick={copyKey}>
              {copied ? "Copied" : "Copy"}
            </button>
          </p>
        ) : (
          <p>Key was only shown at checkout in this browser.</p>
        )}
      </details>

      <p className="postpay__cta-note">
        Want a fixed monthly line with included usage?{" "}
        <Link href="/subscriptions">Pick a commit tier</Link> — $29, $99, or
        $499/mo, each including more metered usage than it costs.
      </p>

      <p className="postpay__cta-note">
        Next: <Link href="/docs/quickstart">Quickstart</Link>
        {" · "}
        <Link href="/connections">Connect other tools</Link>
        {" · "}
        <Link href="/docs/pricing">Metered rates</Link>
        {" · "}
        Teammates can install from{" "}
        <Link href="/i">withohm.dev/i</Link> with their own seat.
      </p>
    </section>
  );
}
