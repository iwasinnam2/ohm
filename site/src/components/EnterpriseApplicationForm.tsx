"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  METER_LABELS,
  PAYG_RATES,
  PROJECTION_VOLUMES,
  formatUsd,
  formatUsdMoney,
  type MeterKey,
} from "@/lib/meterRates";

type MeterFields = {
  expected: string;
  actual: string;
  desiredPpu: string;
};

const emptyMeter = (): MeterFields => ({
  expected: "",
  actual: "",
  desiredPpu: "",
});

const METERS: MeterKey[] = ["cache_hit", "cache_miss", "web_fetch"];

function parseNum(s: string): number {
  const n = Number(s);
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

export function EnterpriseApplicationForm() {
  const [email, setEmail] = useState("");
  const [organisation, setOrganisation] = useState("");
  const [meters, setMeters] = useState<Record<MeterKey, MeterFields>>({
    cache_hit: emptyMeter(),
    cache_miss: emptyMeter(),
    web_fetch: emptyMeter(),
  });
  const [business, setBusiness] = useState("");
  const [termsAck, setTermsAck] = useState(false);
  const [dpaAck, setDpaAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function updateMeter(key: MeterKey, field: keyof MeterFields, value: string) {
    setMeters((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }));
  }

  const projections = useMemo(() => {
    return METERS.map((key) => {
      const ppu = parseNum(meters[key].desiredPpu);
      return {
        key,
        ppu,
        rows: PROJECTION_VOLUMES.map((vol) => ({
          volume: vol,
          monthly: vol * ppu,
        })),
      };
    });
  }, [meters]);

  const maxBar = useMemo(() => {
    let m = 1;
    for (const p of projections) {
      for (const row of p.rows) {
        if (row.monthly > m) m = row.monthly;
      }
    }
    return m;
  }, [projections]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const payload = {
        email,
        organisation,
        meters: Object.fromEntries(
          METERS.map((key) => [
            key,
            {
              expected: parseNum(meters[key].expected),
              actual: parseNum(meters[key].actual),
              desired_ppu: parseNum(meters[key].desiredPpu),
              payg_list: PAYG_RATES[key],
            },
          ]),
        ),
        projections: projections.map((p) => ({
          meter: p.key,
          desired_ppu: p.ppu,
          steps: p.rows,
        })),
        business,
        terms_ack: termsAck,
        dpa_ack: dpaAck,
      };
      const res = await fetch("/api/enterprise/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
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
        <h2 className="enterprise-success__title">Application successful</h2>
        <p className="enterprise-success__lede">
          Admin reviews applications within 2–4 working days. Based on day of
          submission, expect an email response within this timeframe. Until then,
          search your inbox for an email on how to join the enterprise
          design-partner forum, where you can contact devs and other enterprise
          members directly.
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

      <fieldset className="enterprise-meters" disabled={busy}>
        <legend>Transaction usage agreements</legend>
        <p className="enterprise-meters__hint">
          Actual monthly usage must be sourced from your Cursor / used interface
          over prior months of your own personal usage — not estimates alone.
        </p>

        {METERS.map((key) => (
          <div key={key} className="enterprise-meter">
            <h3 className="enterprise-meter__title">{METER_LABELS[key]}</h3>
            <div className="enterprise-meter__grid">
              <label className="billing-form__field">
                <span>Expected monthly usage</span>
                <input
                  type="number"
                  min={0}
                  step={1}
                  inputMode="numeric"
                  value={meters[key].expected}
                  onChange={(e) => updateMeter(key, "expected", e.target.value)}
                  placeholder="e.g. 5000"
                  required
                />
              </label>
              <label className="billing-form__field">
                <span>Actual monthly usage</span>
                <input
                  type="number"
                  min={0}
                  step={1}
                  inputMode="numeric"
                  value={meters[key].actual}
                  onChange={(e) => updateMeter(key, "actual", e.target.value)}
                  placeholder="From Cursor / prior months"
                  required
                />
              </label>
              <label className="billing-form__field billing-form__field--ppu">
                <span>Desired price per unit (USD)</span>
                <input
                  type="number"
                  min={0}
                  step="0.0001"
                  inputMode="decimal"
                  value={meters[key].desiredPpu}
                  onChange={(e) =>
                    updateMeter(key, "desiredPpu", e.target.value)
                  }
                  placeholder="0.01"
                  required
                />
                <span className="rate-caption">
                  withOhm Intermediate PAYG list:{" "}
                  {formatUsd(PAYG_RATES[key])} per unit. Delivery cost context —
                  negotiated Enterprise rates sit against this published
                  Intermediate meter schedule.
                </span>
              </label>
            </div>
          </div>
        ))}
      </fieldset>

      <section className="projection" aria-label="Monthly cost projection">
        <h3 className="projection__title">Projected monthly transactional cost</h3>
        <p className="projection__axes">
          <strong>Price-Per-Unit</strong> (your desired rate) ×{" "}
          <strong>Monthly Transactional Usage</strong>
        </p>
        <div className="projection__charts">
          {projections.map((p) => (
            <div key={p.key} className="projection__panel">
              <h4 className="projection__meter">{METER_LABELS[p.key]}</h4>
              <p className="projection__ppu">
                PPU {formatUsd(p.ppu)} · at 1,000 units →{" "}
                {formatUsdMoney(1000 * p.ppu)}
              </p>
              <ul className="projection__bars">
                {p.rows.map((row) => {
                  const pct = Math.max(4, (row.monthly / maxBar) * 100);
                  return (
                    <li key={row.volume} className="projection__row">
                      <span className="projection__vol">
                        {row.volume.toLocaleString()} / mo
                      </span>
                      <span className="projection__track">
                        <span
                          className="projection__fill"
                          style={{ width: `${pct}%` }}
                        />
                      </span>
                      <span className="projection__cost">
                        {formatUsdMoney(row.monthly)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <label className="billing-form__field">
        <span>
          Business description — what you do and how you will use withOhm
        </span>
        <textarea
          className="enterprise-textarea"
          value={business}
          onChange={(e) => setBusiness(e.target.value)}
          rows={8}
          required
          minLength={40}
          disabled={busy}
          placeholder="Describe your organisation, AI software workflow, scraping volume, and why you need fixed transactional agreements…"
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

      <button
        type="submit"
        className="btn btn--primary"
        disabled={busy || !termsAck || !dpaAck}
      >
        {busy ? "Sending…" : "Send Application to Admin"}
      </button>
    </form>
  );
}
