"use client";

import { useState } from "react";
import Link from "next/link";

export function SupportQueryForm() {
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await fetch("/api/support/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, subject, message }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(
          data?.error || data?.detail || `Query failed (${res.status})`,
        );
      }
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (success) {
    return (
      <div className="enterprise-success" role="status">
        <h2 className="enterprise-success__title">Query sent</h2>
        <p className="enterprise-success__lede">
          Your query is in the support inbox — replies come from a human to the
          email you provided, usually within 1–2 working days.
        </p>
        <p>
          <Link href="/support">Back to support</Link>
          {" · "}
          <Link href="/">Home</Link>
        </p>
      </div>
    );
  }

  return (
    <form className="billing-form" onSubmit={onSubmit}>
      <label className="billing-form__field">
        <span>Your email</span>
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
        <span>Subject</span>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Billing, metering, setup…"
          maxLength={200}
          required
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Message</span>
        <textarea
          className="enterprise-textarea"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={8}
          minLength={10}
          maxLength={5000}
          required
          disabled={busy}
          placeholder="What happened, what you expected, and any tenant label or invoice reference…"
        />
      </label>

      {error ? (
        <p className="billing-form__error">
          {error} — if this keeps failing, email{" "}
          <a href="mailto:queries@withohm.dev">queries@withohm.dev</a> directly.
        </p>
      ) : null}

      <button type="submit" className="btn btn--primary" disabled={busy}>
        {busy ? "Sending…" : "Send query"}
      </button>
    </form>
  );
}
