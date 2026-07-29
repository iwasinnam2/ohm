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
        One click opens Cursor’s MCP installer with your Ohm seat already wired.
        No JSON to paste. Confirm once — then work with cache replay and
        compliant web context on the pipe.
      </p>

      <div className="postpay__contrast" aria-label="Before and after Ohm">
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
            Add Ohm to Cursor
          </a>
          <p className="postpay__cta-note">
            Opens Cursor → MCP install confirm. Your Ohm key is already in the
            config.
          </p>
        </div>
      ) : (
        <div className="postpay__cta-block">
          <p className="billing-form__error">
            Ohm key missing from this browser session. Start again from{" "}
            <Link href="/billing">billing</Link> so we can wire the one-click
            install.
          </p>
        </div>
      )}

      <details className="postpay__key">
        <summary>Your Ohm API key</summary>
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
    </section>
  );
}
