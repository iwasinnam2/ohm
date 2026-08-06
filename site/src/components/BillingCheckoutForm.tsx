"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { persistKey } from "@/lib/keyStorage";

const FORM_STORAGE = "ohm_checkout_form";

export function BillingCheckoutForm({ commit = "" }: { commit?: string }) {
  const [organisation, setOrganisation] = useState("");
  const [email, setEmail] = useState("");
  const [termsAck, setTermsAck] = useState(false);
  const [dpaAck, setDpaAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState(false);
  const [issuedKey, setIssuedKey] = useState<string | null>(null);
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // A failed attempt (rate limit, network blip, back button from Stripe)
  // must never cost the visitor their typing — restore email/label.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(FORM_STORAGE);
      if (raw) {
        const saved = JSON.parse(raw) as { email?: string; label?: string };
        if (saved.email) setEmail(saved.email);
        if (saved.label) setOrganisation(saved.label);
      }
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(
        FORM_STORAGE,
        JSON.stringify({ email, label: organisation }),
      );
    } catch {
      /* ignore */
    }
  }, [email, organisation]);

  async function copyKey() {
    if (!issuedKey) return;
    try {
      await navigator.clipboard.writeText(issuedKey);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      /* ignore */
    }
  }

  function continueToStripe() {
    if (!checkoutUrl) return;
    window.location.href = checkoutUrl;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setRateLimited(false);
    setBusy(true);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: "payg",
          commit,
          label: organisation,
          email,
          terms_ack: termsAck,
          dpa_ack: dpaAck,
          cancel_url: `${window.location.origin}/billing/cancel`,
          success_url: `${window.location.origin}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setRateLimited(true);
          throw new Error(
            "You've hit our once-in-a-while safety limit on new checkouts " +
              "from one connection. Nothing is wrong with your details — " +
              "they're saved. Wait about a minute and press the button again.",
          );
        }
        const detail = data?.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : detail?.message || data?.error || `Checkout failed (${res.status})`;
        throw new Error(msg);
      }
      const key = data.api_key as string;
      const url = data.checkout?.url as string | undefined;
      if (!key) {
        throw new Error("API key missing from checkout response.");
      }
      if (!url) {
        throw new Error(
          "Checkout URL missing — Stripe may be unconfigured on the API.",
        );
      }
      persistKey(key);
      setIssuedKey(key);
      setCheckoutUrl(url);
      setBusy(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  // Gate: key issued — do not auto-redirect. User must save, then continue.
  if (issuedKey && checkoutUrl) {
    return (
      <div className="billing-form billing-form--key-gate" role="status">
        <h2 className="billing-form__gate-title">Save your withOhm key</h2>
        <p className="billing-form__gate-lede">
          This is shown once. Copy it before you continue to Stripe — we cannot
          email it again. After card setup you&apos;ll land on a success page
          that also keeps it in this browser.
        </p>
        <div className="billing-form__key-panel">
          <code className="billing-form__key-code">{issuedKey}</code>
          <button type="button" className="btn btn--primary" onClick={copyKey}>
            {copied ? "Copied" : "Copy key"}
          </button>
        </div>
        <button
          type="button"
          className="btn btn--primary"
          onClick={continueToStripe}
        >
          I&apos;ve saved it — continue to Stripe
        </button>
        <p className="billing-form__note">
          Tip: paste into a password manager now. After Stripe, open{" "}
          <Link href="/demo">the hit ratio demo</Link> with this key.
        </p>
      </div>
    );
  }

  return (
    <form className="billing-form" onSubmit={onSubmit}>
      <label className="billing-form__field">
        <span>Work email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
          autoComplete="email"
          required
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Organisation name</span>
        <input
          type="text"
          value={organisation}
          onChange={(e) => setOrganisation(e.target.value)}
          placeholder="Acme Labs"
          autoComplete="organization"
          required
          disabled={busy}
        />
      </label>
      <label className="billing-form__check">
        <input
          type="checkbox"
          checked={termsAck}
          onChange={(e) => setTermsAck(e.target.checked)}
          disabled={busy}
          required
        />
        <span>
          I agree to the <Link href="/docs/terms">Terms</Link>
        </span>
      </label>
      <label className="billing-form__check">
        <input
          type="checkbox"
          checked={dpaAck}
          onChange={(e) => setDpaAck(e.target.checked)}
          disabled={busy}
          required
        />
        <span>
          I agree to the <Link href="/docs/dpa">DPA</Link>
        </span>
      </label>
      {error ? (
        <p className="billing-form__error" role="alert">
          {error}
          {!rateLimited ? (
            <>
              {" "}
              Stuck? <Link href="/support">Support</Link> or{" "}
              <a href="mailto:queries@withohm.dev">queries@withohm.dev</a>.
            </>
          ) : null}
        </p>
      ) : null}
      <button
        type="submit"
        className="btn btn--primary"
        disabled={busy || !termsAck || !dpaAck}
      >
        {busy ? "Issuing key…" : "Get key & continue"}
      </button>
      <p className="billing-form__note">
        We issue your <code>sk-at-…</code> key first and pause so you can copy
        it — then Stripe for the card on file. Membership is $0 at checkout;
        usage meters invoice later (see rates below). Model tokens stay on your
        provider keys (BYOK).
      </p>
    </form>
  );
}
