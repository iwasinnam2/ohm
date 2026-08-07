"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { OhmMark } from "@/components/OhmMark";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";
import { persistKey, readStoredKey } from "@/lib/keyStorage";
import { markSeatActivated, writeProfile, readCheckoutForm } from "@/lib/profileStorage";

type ClaimState = "loading" | "ready" | "claimed" | "error";

function BillingSuccessInner() {
  const searchParams = useSearchParams();
  const sessionId = (searchParams.get("session_id") || "").trim();

  const [apiKey, setApiKey] = useState<string | null>(null);
  const [upstreamKey, setUpstreamKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [claimState, setClaimState] = useState<ClaimState>("loading");
  const [claimError, setClaimError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;

    async function claim() {
      if (!sessionId.startsWith("cs_")) {
        const existing = readStoredKey();
        if (existing) {
          setApiKey(existing);
          setClaimState("ready");
        } else {
          setClaimState("error");
          setClaimError(
            "Missing Checkout session. Open API keys if you already saved a key.",
          );
        }
        return;
      }

      while (!cancelled && attempts < 12) {
        attempts += 1;
        try {
          const res = await fetch("/api/pipe/v1/billing/claim-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
          });
          const data = await res.json().catch(() => ({}));
          if (res.ok && typeof data.api_key === "string") {
            persistKey(data.api_key);
            const form = readCheckoutForm();
            if (form) writeProfile(form);
            markSeatActivated();
            if (!cancelled) {
              setApiKey(data.api_key);
              setClaimState("ready");
            }
            return;
          }
          if (res.status === 410) {
            const existing = readStoredKey();
            if (!cancelled) {
              if (existing) {
                setApiKey(existing);
                setClaimState("ready");
              } else {
                setClaimState("claimed");
                setClaimError(
                  typeof data?.detail === "object"
                    ? data.detail?.message
                    : "Key already revealed. Open API keys with a saved secret, or mint another there.",
                );
              }
            }
            return;
          }
          if (res.status === 409) {
            await new Promise((r) => window.setTimeout(r, 1500));
            continue;
          }
          const detail = data?.detail;
          const msg =
            typeof detail === "string"
              ? detail
              : detail?.message || data?.error?.message || `HTTP ${res.status}`;
          if (!cancelled) {
            setClaimState("error");
            setClaimError(msg);
          }
          return;
        } catch (err) {
          if (!cancelled) {
            setClaimState("error");
            setClaimError(err instanceof Error ? err.message : String(err));
          }
          return;
        }
      }
      if (!cancelled) {
        setClaimState("error");
        setClaimError(
          "Still activating your seat — refresh in a few seconds, or check API keys.",
        );
      }
    }

    void claim();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

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
        Issued after Checkout. Copy it now — we only show the secret once.
        Manage and mint more anytime under API keys.
      </p>

      {claimState === "loading" ? (
        <p className="postpay__cta-note">Activating your seat and issuing a key…</p>
      ) : null}

      {apiKey ? (
        <div className="billing-form__key-panel postpay__key-hero">
          <code className="billing-form__key-code">{apiKey}</code>
          <button type="button" className="btn btn--primary" onClick={copyKey}>
            {copied ? "Copied" : "Copy key"}
          </button>
        </div>
      ) : null}

      {claimError ? (
        <p className="billing-form__error" role="alert">
          {claimError}{" "}
          <Link href="/keys">API keys</Link>
          {" · "}
          <Link href="/billing/intermediate">Checkout</Link>
        </p>
      ) : null}

      <div className="cta-row postpay__next">
        <Link href="/profile" className="btn btn--primary">
          Open profile
        </Link>
        <Link href="/keys" className="btn">
          Manage API keys
        </Link>
        <Link href="/workbench" className="btn">
          Open Agent Shell
        </Link>
        <Link href="/demo" className="btn">
          Shell demo
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
        Once cache hits accrue, mint a public receipt, post it with a clear
        headline (e.g. &quot;My monthly savings simply from choosing
        withOhm&quot;), then email the <em>social post URL</em> for the{" "}
        <Link href="/bounty">$100 artifact bounty</Link>.
      </p>

      <p className="postpay__cta-note">
        <Link href="/org">Analytics</Link>
        {" · "}
        <Link href="/docs/pricing">Metered rates</Link>
        {" · "}
        <Link href="/i">Install path</Link>
      </p>
    </section>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense fallback={<p className="postpay__cta-note">Loading…</p>}>
      <BillingSuccessInner />
    </Suspense>
  );
}
