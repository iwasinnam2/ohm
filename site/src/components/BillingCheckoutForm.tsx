"use client";

import { useState } from "react";
import Link from "next/link";

const KEY_STORAGE = "ohm_api_key";

export function BillingCheckoutForm() {
  const [plan, setPlan] = useState<"payg" | "enterprise">("payg");
  const [label, setLabel] = useState("");
  const [email, setEmail] = useState("");
  const [termsAck, setTermsAck] = useState(false);
  const [dpaAck, setDpaAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issuedKey, setIssuedKey] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan,
          label,
          email,
          terms_ack: termsAck,
          dpa_ack: dpaAck,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        const detail = data?.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : detail?.message || data?.error || `Checkout failed (${res.status})`;
        throw new Error(msg);
      }
      const key = data.api_key as string;
      const url = data.checkout?.url as string | undefined;
      if (key) {
        try {
          sessionStorage.setItem(KEY_STORAGE, key);
        } catch {
          /* ignore */
        }
        setIssuedKey(key);
      }
      if (url) {
        window.location.href = url;
        return;
      }
      throw new Error("Checkout URL missing — Stripe may be unconfigured on the API.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <form className="billing-form" onSubmit={onSubmit}>
      <label className="billing-form__field">
        <span>Plan</span>
        <select
          value={plan}
          onChange={(e) => setPlan(e.target.value as "payg" | "enterprise")}
          disabled={busy}
        >
          <option value="payg">PAYG seat — pipe access</option>
          <option value="enterprise">Enterprise — managed capacity</option>
        </select>
      </label>
      <label className="billing-form__field">
        <span>Work email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
          autoComplete="email"
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Label (optional)</span>
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="team name"
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
      {error ? <p className="billing-form__error">{error}</p> : null}
      {issuedKey ? (
        <p className="billing-form__key">
          withOhm key (store now): <code>{issuedKey}</code>
        </p>
      ) : null}
      <button type="submit" className="btn btn--primary" disabled={busy || !termsAck || !dpaAck}>
        {busy ? "Redirecting…" : "Continue to Checkout"}
      </button>
      <p className="billing-form__note">
        After you pay, one button adds withOhm to Cursor — seat wired, no JSON
        to assemble. Model tokens stay on your provider keys (BYOK).{" "}
        <Link href="/docs/pricing">Pricing</Link>
      </p>
    </form>
  );
}
