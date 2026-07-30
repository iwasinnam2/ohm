"use client";

import { useState } from "react";

type Props = {
  apiKey: string | null;
};

export function CreditPackTopup({ apiKey }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startTopup() {
    if (!apiKey) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/billing/topup", {
        method: "POST",
        headers: { Authorization: `Bearer ${apiKey}` },
      });
      const data = (await res.json()) as {
        checkout?: { url?: string };
        error?: { message?: string } | string;
      };
      const url = data.checkout?.url;
      if (!res.ok || !url) {
        const msg =
          typeof data.error === "string"
            ? data.error
            : data.error?.message || `Top-up failed (${res.status})`;
        throw new Error(msg);
      }
      window.location.assign(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  }

  if (!apiKey) return null;

  return (
    <div className="postpay__cta-block">
      <button
        type="button"
        className="btn btn--ghost"
        onClick={startTopup}
        disabled={busy}
      >
        {busy ? "Opening Checkout…" : "Prepay $29 credit pack"}
      </button>
      <p className="postpay__cta-note">
        Optional — credits your balance against future metered invoices.
      </p>
      {error ? <p className="billing-form__error">{error}</p> : null}
    </div>
  );
}
