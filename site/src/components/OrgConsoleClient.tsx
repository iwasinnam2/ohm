"use client";

import { useCallback, useState } from "react";

const API = (
  process.env.NEXT_PUBLIC_OHM_API_URL || "https://api.withohm.dev"
).replace(/\/$/, "");

export function OrgConsoleClient() {
  const [apiKey, setApiKey] = useState("");
  const [session, setSession] = useState("");
  const [orgName, setOrgName] = useState("My org");
  const [email, setEmail] = useState("you@company.com");
  const [log, setLog] = useState("");
  const [busy, setBusy] = useState(false);

  const headers = useCallback(() => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (session) h["X-Ohm-Session"] = session;
    else if (apiKey) h.Authorization = `Bearer ${apiKey}`;
    return h;
  }, [apiKey, session]);

  async function createOrg() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/org`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          name: orgName,
          owner_email: email,
          terms_ack: true,
          dpa_ack: true,
        }),
      });
      const data = await res.json();
      setLog(JSON.stringify(data, null, 2));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadLedger() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/org/ledger`, { headers: headers() });
      setLog(JSON.stringify(await res.json(), null, 2));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function exportCsv() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/org/ledger/export?format=csv`, {
        headers: headers(),
      });
      const text = await res.text();
      setLog(text.slice(0, 4000));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadAudit() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/org/audit`, { headers: headers() });
      setLog(JSON.stringify(await res.json(), null, 2));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="org-console">
      <label className="billing-form__field">
        <span>API key (org-bound)</span>
        <input
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-at-…"
          autoComplete="off"
        />
      </label>
      <label className="billing-form__field">
        <span>SSO session (optional)</span>
        <input
          value={session}
          onChange={(e) => setSession(e.target.value)}
          placeholder="X-Ohm-Session token"
          autoComplete="off"
        />
      </label>
      <label className="billing-form__field">
        <span>Org name</span>
        <input value={orgName} onChange={(e) => setOrgName(e.target.value)} />
      </label>
      <label className="billing-form__field">
        <span>Owner email</span>
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <div className="cta-row">
        <button
          type="button"
          className="btn btn--primary"
          disabled={busy || !apiKey}
          onClick={createOrg}
        >
          Create org
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || (!apiKey && !session)}
          onClick={loadLedger}
        >
          Ledger
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || (!apiKey && !session)}
          onClick={exportCsv}
        >
          Export CSV
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || (!apiKey && !session)}
          onClick={loadAudit}
        >
          Audit
        </button>
      </div>
      <pre className="org-console__log">{log || "Responses appear here."}</pre>
      <p className="receipt__foot">
        Docs:{" "}
        <a href="https://github.com/iwasinnam2/ohm/blob/master/docs/ENTERPRISE_CHAOS.md">
          ENTERPRISE_CHAOS.md
        </a>
      </p>
    </div>
  );
}
