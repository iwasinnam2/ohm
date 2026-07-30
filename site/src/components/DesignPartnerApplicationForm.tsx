"use client";

import { useState } from "react";
import Link from "next/link";

const PAINS = [
  { id: "cache", label: "Duplicate prompts / want prompt cache replay" },
  { id: "browse", label: "Agents blocked on manual web browse / scrape" },
  { id: "limits", label: "Provider rate limits / wait relief" },
  { id: "mcp", label: "Want a clean Cursor MCP attach for the pipe" },
] as const;

export function DesignPartnerApplicationForm() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [organisation, setOrganisation] = useState("");
  const [handle, setHandle] = useState("");
  const [pains, setPains] = useState<string[]>([]);
  const [useCase, setUseCase] = useState("");
  const [termsAck, setTermsAck] = useState(false);
  const [dpaAck, setDpaAck] = useState(false);
  const [quoteOk, setQuoteOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function togglePain(id: string) {
    setPains((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await fetch("/api/design-partners/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          name,
          organisation,
          handle,
          pains,
          use_case: useCase,
          terms_ack: termsAck,
          dpa_ack: dpaAck,
          quote_ok: quoteOk,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(
          data?.error || data?.detail || `Application failed (${res.status})`,
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
        <h2 className="enterprise-success__title">Application received</h2>
        <p className="enterprise-success__lede">
          We review founding design-partner applications within 2–4 working days
          and reply from partners@withohm.dev with a key and Cursor MCP attach
          steps. Solo builders welcome — you do not need a company.
        </p>
        <p>
          Want to start immediately?{" "}
          <Link href="/billing/intermediate">Start Intermediate</Link>{" "}
          ($0 membership + card on file), then use{" "}
          <strong>Add withOhm to Cursor</strong> on the success screen.
        </p>
        <p>
          <Link href="/subscriptions">Back to subscriptions</Link>
        </p>
      </div>
    );
  }

  return (
    <form className="billing-form enterprise-form" onSubmit={onSubmit}>
      <label className="billing-form__field">
        <span>Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com or personal"
          autoComplete="email"
          required
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Your name</span>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ada"
          autoComplete="name"
          required
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Organisation (optional — solo is fine)</span>
        <input
          type="text"
          value={organisation}
          onChange={(e) => setOrganisation(e.target.value)}
          placeholder="Indie / Acme Labs"
          autoComplete="organization"
          disabled={busy}
        />
      </label>
      <label className="billing-form__field">
        <span>Cursor Forum / Discord / X handle (optional)</span>
        <input
          type="text"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          placeholder="@you"
          disabled={busy}
        />
      </label>

      <fieldset className="enterprise-meters" disabled={busy}>
        <legend>What hurts today? (pick any)</legend>
        {PAINS.map((p) => (
          <label key={p.id} className="billing-form__check">
            <input
              type="checkbox"
              checked={pains.includes(p.id)}
              onChange={() => togglePain(p.id)}
            />
            <span>{p.label}</span>
          </label>
        ))}
      </fieldset>

      <label className="billing-form__field">
        <span>How you use Cursor / agents (2–3 sentences)</span>
        <textarea
          className="enterprise-textarea"
          value={useCase}
          onChange={(e) => setUseCase(e.target.value)}
          rows={6}
          required
          minLength={40}
          disabled={busy}
          placeholder="e.g. I build agents in Cursor that need public docs in context; I also re-hit the same prompts a lot and want cache replay…"
        />
      </label>

      <label className="billing-form__check">
        <input
          type="checkbox"
          checked={quoteOk}
          onChange={(e) => setQuoteOk(e.target.checked)}
          disabled={busy}
          required
        />
        <span>
          I agree to share one public quote and a `/v1/usage` snapshot after
          about a week of use (founding-partner exchange)
        </span>
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

      <button
        type="submit"
        className="btn btn--primary"
        disabled={busy || !termsAck || !dpaAck || !quoteOk}
      >
        {busy ? "Sending…" : "Apply for founding seat"}
      </button>
    </form>
  );
}
