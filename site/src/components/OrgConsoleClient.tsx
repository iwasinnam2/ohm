"use client";

import { useCallback, useState } from "react";

const API = "/api/pipe";

function currentUtcMonth(): string {
  const d = new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

type HitGroup = {
  cache_hits?: number;
  cache_misses?: number;
  hit_ratio?: number | null;
  pipe_rent_usd?: number;
  estimated_provider_avoided_usd?: number;
};

export function OrgConsoleClient() {
  const [apiKey, setApiKey] = useState("");
  const [session, setSession] = useState("");
  const [orgName, setOrgName] = useState("My org");
  const [email, setEmail] = useState("you@company.com");
  const [month, setMonth] = useState(currentUtcMonth);
  const [groupBy, setGroupBy] = useState<"cost_center" | "path">("path");
  const [hitRatioJson, setHitRatioJson] = useState("");
  const [capUsd, setCapUsd] = useState("0");
  const [capMode, setCapMode] = useState<"soft" | "hard">("soft");
  const [capOverrides, setCapOverrides] = useState("");
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

  async function loadStatement() {
    setBusy(true);
    try {
      const q = encodeURIComponent(month.trim() || currentUtcMonth());
      const res = await fetch(`${API}/v1/org/ledger/statement?month=${q}`, {
        headers: headers(),
      });
      setLog(JSON.stringify(await res.json(), null, 2));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function loadHitRatio() {
    setBusy(true);
    try {
      const q = encodeURIComponent(month.trim() || currentUtcMonth());
      const res = await fetch(
        `${API}/v1/org/ledger/hit-ratio?month=${q}&group_by=${groupBy}`,
        { headers: headers() }
      );
      const data = await res.json();
      const pretty = JSON.stringify(data, null, 2);
      setHitRatioJson(pretty);
      setLog(pretty);
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveSpendCaps() {
    setBusy(true);
    try {
      let byCc: Record<string, number> | undefined;
      const raw = capOverrides.trim();
      if (raw) {
        byCc = JSON.parse(raw) as Record<string, number>;
      }
      const body: Record<string, unknown> = {
        spend_cap_usd_month: Number(capUsd) || 0,
        spend_cap_mode: capMode,
      };
      if (byCc) body.spend_caps_by_cost_center = byCc;
      const res = await fetch(`${API}/v1/org/policy`, {
        method: "PUT",
        headers: headers(),
        body: JSON.stringify(body),
      });
      setLog(JSON.stringify(await res.json(), null, 2));
    } catch (e) {
      setLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function downloadMonthCsv() {
    setBusy(true);
    try {
      const q = encodeURIComponent(month.trim() || currentUtcMonth());
      const res = await fetch(
        `${API}/v1/org/ledger/export?format=csv&month=${q}`,
        { headers: headers() }
      );
      const text = await res.text();
      if (!res.ok) {
        setLog(text.slice(0, 4000));
        return;
      }
      const blob = new Blob([text], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ohm-ledger-${q}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setLog(`Downloaded CSV for ${q} (${text.split("\n").length - 1} data rows).`);
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

  let hitGroups: Record<string, HitGroup> | null = null;
  try {
    if (hitRatioJson) {
      const parsed = JSON.parse(hitRatioJson) as { groups?: Record<string, HitGroup> };
      hitGroups = parsed.groups || null;
    }
  } catch {
    hitGroups = null;
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
      <label className="billing-form__field">
        <span>Statement month (UTC)</span>
        <input
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          placeholder="YYYY-MM"
          autoComplete="off"
        />
      </label>

      <section className="org-console__panel">
        <h2>Hit ratio</h2>
        <p className="receipt__foot">
          Inventory by cost center or traffic path (X-Ohm-Path). Estimates only —
          Ohm invoice ≠ provider bill.
        </p>
        <div className="cta-row">
          <label>
            Group by{" "}
            <select
              value={groupBy}
              onChange={(e) =>
                setGroupBy(e.target.value === "path" ? "path" : "cost_center")
              }
            >
              <option value="path">path</option>
              <option value="cost_center">cost_center</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy || (!apiKey && !session)}
            onClick={loadHitRatio}
          >
            Load hit ratio
          </button>
          <button
            type="button"
            className="btn"
            disabled={!hitRatioJson}
            onClick={() => navigator.clipboard?.writeText(hitRatioJson)}
          >
            Copy JSON
          </button>
        </div>
        {hitGroups ? (
          <table className="org-console__table">
            <thead>
              <tr>
                <th>{groupBy}</th>
                <th>hits</th>
                <th>misses</th>
                <th>ratio</th>
                <th>pipe $</th>
                <th>avoided $*</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(hitGroups).map(([name, g]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td>{g.cache_hits ?? 0}</td>
                  <td>{g.cache_misses ?? 0}</td>
                  <td>
                    {g.hit_ratio == null
                      ? "—"
                      : `${(g.hit_ratio * 100).toFixed(1)}%`}
                  </td>
                  <td>{g.pipe_rent_usd ?? 0}</td>
                  <td>{g.estimated_provider_avoided_usd ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>

      <section className="org-console__panel">
        <h2>Spend caps (MISS soft-stop)</h2>
        <p className="receipt__foot">
          Caps meter pipe rent USD this UTC month per cost center. Soft allows
          MISS with headers; hard returns 402. HITs always serve. Caps ≠ credits.
        </p>
        <label className="billing-form__field">
          <span>Monthly cap USD (0 = off)</span>
          <input
            value={capUsd}
            onChange={(e) => setCapUsd(e.target.value)}
            inputMode="decimal"
          />
        </label>
        <label className="billing-form__field">
          <span>Mode</span>
          <select
            value={capMode}
            onChange={(e) =>
              setCapMode(e.target.value === "hard" ? "hard" : "soft")
            }
          >
            <option value="soft">soft</option>
            <option value="hard">hard</option>
          </select>
        </label>
        <label className="billing-form__field">
          <span>Per–cost-center overrides (JSON)</span>
          <input
            value={capOverrides}
            onChange={(e) => setCapOverrides(e.target.value)}
            placeholder='{"ci-prompts": 25}'
            autoComplete="off"
          />
        </label>
        <button
          type="button"
          className="btn"
          disabled={busy || (!apiKey && !session)}
          onClick={saveSpendCaps}
        >
          Save spend caps
        </button>
      </section>

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
          onClick={loadStatement}
        >
          This month statement
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || (!apiKey && !session)}
          onClick={downloadMonthCsv}
        >
          Download month CSV
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
        <a href="https://github.com/iwasinnam2/ohm/blob/master/docs/ENTERPRISE.md">
          ENTERPRISE.md (FinOps)
        </a>
      </p>
    </div>
  );
}
