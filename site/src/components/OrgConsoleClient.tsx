"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { persistKey, readStoredKey } from "@/lib/keyStorage";
import {
  COMMIT_TIERS,
  formatUsd,
  formatUsdMoney,
  PAYG_RATES,
} from "@/lib/meterRates";

const API = "/api/pipe";

function currentUtcMonth(): string {
  const d = new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

function planLabel(plan: string | undefined): string {
  switch ((plan || "").toLowerCase()) {
    case "payg":
      return "Intermediate";
    case "enterprise":
      return "Enterprise";
    case "design_partner":
      return "Design partner";
    case "dev":
      return "Dev";
    default:
      return plan || "—";
  }
}

type UsageSnap = {
  plan?: string;
  status?: string;
  billing_paid?: boolean;
  usage_unlocked?: boolean;
  invoice_basis?: string;
  byok?: boolean;
  billing_model?: string;
  cache_hit_ratio?: number;
  cache_hit_tokens?: number;
  cache_miss_tokens?: number;
  cache_hit_usd?: number;
  cache_miss_usd?: number;
  fetches?: number;
  fetch_usd?: number;
  requests?: number;
  revenue_usd?: number;
  today_cache_hit_tokens?: number;
  today_cache_miss_tokens?: number;
  today_fetches?: number;
  today_cache_hit_usd?: number;
  today_cache_miss_usd?: number;
  today_fetch_usd?: number;
  stripe_synced?: boolean;
  ledger_day?: string;
  tenant?: string;
};

type SavingsSnap = {
  plan?: string;
  cache_hit_ratio?: number;
  estimated_provider_avoided_usd?: number;
  pipe_rent_usd?: number;
  ohm_pipe_rent_usd?: number;
  roi_ratio?: number | null;
  message?: string;
};

type HitGroup = {
  cache_hits?: number;
  cache_misses?: number;
  hit_ratio?: number | null;
  pipe_rent_usd?: number;
  estimated_provider_avoided_usd?: number;
};

type OrgView = {
  org_id?: string;
  name?: string;
  plan?: string;
  status?: string;
  cost_centers?: string[];
  member_count?: number;
  policy?: {
    spend_cap_usd_month?: number;
    spend_cap_mode?: string;
    spend_caps_by_cost_center?: Record<string, number>;
    managed_keys?: boolean;
    model_allowlist?: string[];
  };
};

type DashError = string | null;

function num(n: unknown): number {
  return typeof n === "number" && Number.isFinite(n) ? n : 0;
}

function pct(ratio: number | null | undefined): string {
  if (ratio == null || !Number.isFinite(ratio)) return "—";
  return `${(ratio * 100).toFixed(1)}%`;
}

export function OrgConsoleClient() {
  const [apiKey, setApiKey] = useState("");
  const [session, setSession] = useState("");
  const [month, setMonth] = useState(currentUtcMonth);
  const [groupBy, setGroupBy] = useState<"cost_center" | "path">("path");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<DashError>(null);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);

  const [usage, setUsage] = useState<UsageSnap | null>(null);
  const [savings, setSavings] = useState<SavingsSnap | null>(null);
  const [org, setOrg] = useState<OrgView | null>(null);
  const [hitGroups, setHitGroups] = useState<Record<string, HitGroup> | null>(
    null,
  );
  const [statementNote, setStatementNote] = useState("");

  // Admin / config
  const [orgName, setOrgName] = useState("My org");
  const [email, setEmail] = useState("");
  const [capUsd, setCapUsd] = useState("0");
  const [capMode, setCapMode] = useState<"soft" | "hard">("soft");
  const [capOverrides, setCapOverrides] = useState("");
  const [adminLog, setAdminLog] = useState("");

  const authHeaders = useCallback((): HeadersInit => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (session.trim()) h["X-Ohm-Session"] = session.trim();
    else if (apiKey.trim()) h.Authorization = `Bearer ${apiKey.trim()}`;
    return h;
  }, [apiKey, session]);

  const canQuery = Boolean(apiKey.trim() || session.trim());

  const refresh = useCallback(async () => {
    if (!apiKey.trim() && !session.trim()) {
      setError("Paste a withOhm key (sk-at-…) to load analytics.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const headers = authHeaders();
      const keyHeaders: HeadersInit = apiKey.trim()
        ? { Authorization: `Bearer ${apiKey.trim()}` }
        : headers;

      const [usageRes, savingsRes, orgRes, hitRes] = await Promise.all([
        apiKey.trim()
          ? fetch(`${API}/v1/usage`, { headers: keyHeaders, cache: "no-store" })
          : Promise.resolve(null),
        apiKey.trim()
          ? fetch(`${API}/v1/savings`, {
              headers: keyHeaders,
              cache: "no-store",
            })
          : Promise.resolve(null),
        fetch(`${API}/v1/org`, { headers, cache: "no-store" }),
        // Prefer org hit-ratio; fall back to tenant
        fetch(
          `${API}/v1/org/ledger/hit-ratio?month=${encodeURIComponent(month)}&group_by=${groupBy}`,
          { headers, cache: "no-store" },
        ).then(async (res) => {
          if (res.ok) return res;
          if (!apiKey.trim()) return res;
          return fetch(
            `${API}/v1/ledger/hit-ratio?month=${encodeURIComponent(month)}&group_by=${groupBy}`,
            { headers: keyHeaders, cache: "no-store" },
          );
        }),
      ]);

      if (usageRes) {
        const data = await usageRes.json().catch(() => ({}));
        if (!usageRes.ok) {
          throw new Error(
            typeof data.detail === "string"
              ? data.detail
              : data.error?.message || `Usage failed (${usageRes.status})`,
          );
        }
        setUsage(data as UsageSnap);
      }

      if (savingsRes) {
        const data = await savingsRes.json().catch(() => ({}));
        if (savingsRes.ok) setSavings(data as SavingsSnap);
        else setSavings(null);
      }

      if (orgRes.ok) {
        const data = await orgRes.json();
        const view = (data.org || data) as OrgView;
        setOrg(view);
        if (view.policy?.spend_cap_usd_month != null) {
          setCapUsd(String(view.policy.spend_cap_usd_month));
        }
        if (view.policy?.spend_cap_mode === "hard") setCapMode("hard");
        if (view.policy?.spend_caps_by_cost_center) {
          setCapOverrides(
            JSON.stringify(view.policy.spend_caps_by_cost_center),
          );
        }
      } else {
        setOrg(null);
      }

      if (hitRes.ok) {
        const data = await hitRes.json();
        setHitGroups(
          (data.groups as Record<string, HitGroup> | undefined) || {},
        );
        setStatementNote(
          data.estimate_only
            ? "Breakdown estimates — Ohm invoice ≠ provider bill."
            : "",
        );
      } else {
        setHitGroups(null);
      }

      setLoadedAt(new Date().toISOString());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiKey, session, month, groupBy, authHeaders]);

  useEffect(() => {
    const stored = readStoredKey();
    if (stored) setApiKey(stored);
  }, []);

  useEffect(() => {
    if (apiKey.trim().startsWith("sk-at-") || session.trim()) {
      void refresh();
    }
  }, [apiKey, session, refresh]);

  function onKeyChange(value: string) {
    setApiKey(value);
    if (value.trim().startsWith("sk-at-")) persistKey(value.trim());
  }

  const pipeRent = useMemo(() => {
    if (savings) {
      return num(
        savings.pipe_rent_usd ??
          savings.ohm_pipe_rent_usd ??
          usage?.revenue_usd,
      );
    }
    return num(usage?.revenue_usd);
  }, [savings, usage]);

  const avoided = num(savings?.estimated_provider_avoided_usd);
  const hitRatio = usage?.cache_hit_ratio ?? savings?.cache_hit_ratio ?? null;

  async function createOrg() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/v1/org`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          name: orgName,
          owner_email: email || "you@company.com",
          terms_ack: true,
          dpa_ack: true,
        }),
      });
      const data = await res.json();
      setAdminLog(JSON.stringify(data, null, 2));
      await refresh();
    } catch (e) {
      setAdminLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveSpendCaps() {
    setBusy(true);
    try {
      let byCc: Record<string, number> | undefined;
      const raw = capOverrides.trim();
      if (raw) byCc = JSON.parse(raw) as Record<string, number>;
      const body: Record<string, unknown> = {
        spend_cap_usd_month: Number(capUsd) || 0,
        spend_cap_mode: capMode,
      };
      if (byCc) body.spend_caps_by_cost_center = byCc;
      const res = await fetch(`${API}/v1/org/policy`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setAdminLog(JSON.stringify(data, null, 2));
      await refresh();
    } catch (e) {
      setAdminLog(String(e));
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
        { headers: authHeaders() },
      );
      const text = await res.text();
      if (!res.ok) {
        setAdminLog(text.slice(0, 4000));
        return;
      }
      const blob = new Blob([text], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ohm-ledger-${q}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setAdminLog(`Downloaded CSV for ${q}.`);
    } catch (e) {
      setAdminLog(String(e));
    } finally {
      setBusy(false);
    }
  }

  const plan = usage?.plan || org?.plan;
  const planName = planLabel(plan);

  return (
    <div className="analytics">
      <section className="analytics__auth" aria-label="Session">
        <label className="analytics__field">
          <span>withOhm key</span>
          <input
            value={apiKey}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder="sk-at-…"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="analytics__field">
          <span>SSO session (optional)</span>
          <input
            value={session}
            onChange={(e) => setSession(e.target.value)}
            placeholder="X-Ohm-Session"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <label className="analytics__field analytics__field--narrow">
          <span>Month (UTC)</span>
          <input
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            placeholder="YYYY-MM"
            autoComplete="off"
          />
        </label>
        <label className="analytics__field analytics__field--narrow">
          <span>Breakdown</span>
          <select
            value={groupBy}
            onChange={(e) =>
              setGroupBy(e.target.value === "path" ? "path" : "cost_center")
            }
          >
            <option value="path">by path</option>
            <option value="cost_center">by cost center</option>
          </select>
        </label>
        <div className="analytics__auth-actions">
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy || !canQuery}
            onClick={() => void refresh()}
          >
            {busy ? "Refreshing…" : "Refresh"}
          </button>
          {loadedAt ? (
            <span className="analytics__stamp">
              Updated {new Date(loadedAt).toLocaleTimeString()}
            </span>
          ) : null}
        </div>
      </section>

      {error ? (
        <p className="analytics__error" role="alert">
          {error}
        </p>
      ) : null}

      {!usage && !error && !busy ? (
        <p className="analytics__empty">
          Connect with your key to load live usage, plan configuration, and
          FinOps tallies from the pipe.
        </p>
      ) : null}

      {usage || org ? (
        <>
          <section className="analytics__plan" aria-labelledby="analytics-plan">
            <div className="analytics__plan-head">
              <div>
                <p className="analytics__eyebrow">Plan configuration</p>
                <h2 id="analytics-plan">{planName}</h2>
                <p className="analytics__plan-sub">
                  {plan === "payg" && (
                    <>
                      $0 Intermediate membership · meters at list · BYOK ·{" "}
                      <code>invoice_basis: {usage?.invoice_basis || "seat_plus_meters"}</code>
                    </>
                  )}
                  {plan === "enterprise" && (
                    <>Negotiated Enterprise · contact us for capacity terms</>
                  )}
                  {plan && plan !== "payg" && plan !== "enterprise" && (
                    <>Plan id <code>{plan}</code></>
                  )}
                </p>
              </div>
              <dl className="analytics__plan-meta">
                <div>
                  <dt>Status</dt>
                  <dd>{usage?.status || org?.status || "—"}</dd>
                </div>
                <div>
                  <dt>Billing</dt>
                  <dd>
                    {usage?.billing_paid
                      ? "Paid / unlocked"
                      : usage?.usage_unlocked
                        ? "Unlocked"
                        : "Awaiting first paid invoice"}
                  </dd>
                </div>
                <div>
                  <dt>Stripe meters</dt>
                  <dd>{usage?.stripe_synced ? "Synced" : "Pending / local"}</dd>
                </div>
                <div>
                  <dt>Org</dt>
                  <dd>
                    {org?.name
                      ? `${org.name} (${org.member_count ?? 0} members)`
                      : "Solo seat — no org yet"}
                  </dd>
                </div>
              </dl>
            </div>
            <div className="analytics__rates">
              <p className="analytics__eyebrow">Meter list (USD)</p>
              <ul>
                <li>
                  Cache hit{" "}
                  <strong>{formatUsd(PAYG_RATES.cache_hit)}/1k</strong>
                </li>
                <li>
                  Cache miss{" "}
                  <strong>{formatUsd(PAYG_RATES.cache_miss)}/1k</strong>
                </li>
                <li>
                  Web fetch{" "}
                  <strong>{formatUsd(PAYG_RATES.web_fetch)}/URL</strong>
                </li>
              </ul>
              <p className="analytics__plan-links">
                Optional commits:{" "}
                {COMMIT_TIERS.map((t) => `${t.id} $${t.usd_month}`).join(" · ")}
                {" · "}
                <Link href="/subscriptions">Subscriptions</Link>
                {" · "}
                <Link href="/pricing">Pricing</Link>
                {" · "}
                <Link href="/billing/enterprise">Enterprise</Link>
              </p>
              {org?.policy ? (
                <p className="analytics__plan-links">
                  Spend cap:{" "}
                  {num(org.policy.spend_cap_usd_month) > 0
                    ? `${formatUsdMoney(num(org.policy.spend_cap_usd_month))}/mo (${org.policy.spend_cap_mode || "soft"})`
                    : "off"}
                  {org.cost_centers?.length
                    ? ` · cost centers: ${org.cost_centers.join(", ")}`
                    : ""}
                </p>
              ) : null}
            </div>
          </section>

          <section aria-labelledby="analytics-kpis">
            <h2 id="analytics-kpis" className="analytics__section-title">
              Usage tallies
            </h2>
            <div className="analytics__kpis">
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Hit ratio</span>
                <strong className="analytics__kpi-value">{pct(hitRatio)}</strong>
                <span className="analytics__kpi-foot">Lifetime tokens</span>
              </div>
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Cache hit tokens</span>
                <strong className="analytics__kpi-value">
                  {Math.round(num(usage?.cache_hit_tokens)).toLocaleString()}
                </strong>
                <span className="analytics__kpi-foot">
                  Today{" "}
                  {Math.round(
                    num(usage?.today_cache_hit_tokens),
                  ).toLocaleString()}
                </span>
              </div>
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Cache miss tokens</span>
                <strong className="analytics__kpi-value">
                  {Math.round(num(usage?.cache_miss_tokens)).toLocaleString()}
                </strong>
                <span className="analytics__kpi-foot">
                  Today{" "}
                  {Math.round(
                    num(usage?.today_cache_miss_tokens),
                  ).toLocaleString()}
                </span>
              </div>
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Web fetches</span>
                <strong className="analytics__kpi-value">
                  {Math.round(num(usage?.fetches)).toLocaleString()}
                </strong>
                <span className="analytics__kpi-foot">
                  Today {Math.round(num(usage?.today_fetches)).toLocaleString()}
                </span>
              </div>
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Pipe rent</span>
                <strong className="analytics__kpi-value">
                  {formatUsdMoney(pipeRent)}
                </strong>
                <span className="analytics__kpi-foot">
                  Hits {formatUsdMoney(num(usage?.cache_hit_usd))} · misses{" "}
                  {formatUsdMoney(num(usage?.cache_miss_usd))} · fetch{" "}
                  {formatUsdMoney(num(usage?.fetch_usd))}
                </span>
              </div>
              <div className="analytics__kpi">
                <span className="analytics__kpi-label">Est. avoided</span>
                <strong className="analytics__kpi-value">
                  {formatUsdMoney(avoided)}
                </strong>
                <span className="analytics__kpi-foot">
                  estimate_only
                  {savings?.roi_ratio != null
                    ? ` · roi ${Number(savings.roi_ratio).toFixed(2)}×`
                    : ""}
                </span>
              </div>
            </div>
          </section>

          <section aria-labelledby="analytics-meters">
            <h2 id="analytics-meters" className="analytics__section-title">
              Meter detail
            </h2>
            <table className="analytics__table">
              <thead>
                <tr>
                  <th>Meter</th>
                  <th>Lifetime</th>
                  <th>Today ({usage?.ledger_day || "UTC"})</th>
                  <th>Billed (lifetime)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Cache hit tokens</td>
                  <td>{Math.round(num(usage?.cache_hit_tokens)).toLocaleString()}</td>
                  <td>
                    {Math.round(
                      num(usage?.today_cache_hit_tokens),
                    ).toLocaleString()}
                  </td>
                  <td>{formatUsdMoney(num(usage?.cache_hit_usd))}</td>
                </tr>
                <tr>
                  <td>Cache miss tokens</td>
                  <td>
                    {Math.round(num(usage?.cache_miss_tokens)).toLocaleString()}
                  </td>
                  <td>
                    {Math.round(
                      num(usage?.today_cache_miss_tokens),
                    ).toLocaleString()}
                  </td>
                  <td>{formatUsdMoney(num(usage?.cache_miss_usd))}</td>
                </tr>
                <tr>
                  <td>Web fetches</td>
                  <td>{Math.round(num(usage?.fetches)).toLocaleString()}</td>
                  <td>
                    {Math.round(num(usage?.today_fetches)).toLocaleString()}
                  </td>
                  <td>{formatUsdMoney(num(usage?.fetch_usd))}</td>
                </tr>
                <tr>
                  <td>Requests</td>
                  <td>{Math.round(num(usage?.requests)).toLocaleString()}</td>
                  <td>—</td>
                  <td>{formatUsdMoney(pipeRent)}</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section aria-labelledby="analytics-breakdown">
            <div className="analytics__section-head">
              <h2 id="analytics-breakdown" className="analytics__section-title">
                Breakdown · {month} · by {groupBy.replace("_", " ")}
              </h2>
              <button
                type="button"
                className="btn"
                disabled={busy || !canQuery}
                onClick={() => void refresh()}
              >
                Reload breakdown
              </button>
            </div>
            {statementNote ? (
              <p className="analytics__note">{statementNote}</p>
            ) : null}
            {hitGroups && Object.keys(hitGroups).length > 0 ? (
              <table className="analytics__table">
                <thead>
                  <tr>
                    <th>{groupBy === "path" ? "Path" : "Cost center"}</th>
                    <th>Hits</th>
                    <th>Misses</th>
                    <th>Ratio</th>
                    <th>Pipe $</th>
                    <th>Avoided $*</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(hitGroups).map(([name, g]) => (
                    <tr key={name}>
                      <td>
                        <code>{name}</code>
                      </td>
                      <td>{g.cache_hits ?? 0}</td>
                      <td>{g.cache_misses ?? 0}</td>
                      <td>{pct(g.hit_ratio)}</td>
                      <td>{formatUsdMoney(num(g.pipe_rent_usd))}</td>
                      <td>
                        {formatUsdMoney(num(g.estimated_provider_avoided_usd))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="analytics__note">
                No grouped traffic for this month yet. Send chat with{" "}
                <code>X-Ohm-Path</code> or use the Agent Shell, then refresh.
              </p>
            )}
          </section>
        </>
      ) : null}

      <details className="analytics__admin">
        <summary>Org setup &amp; exports</summary>
        <div className="analytics__admin-grid">
          <div>
            <h3>Create org</h3>
            <label className="analytics__field">
              <span>Org name</span>
              <input
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            </label>
            <label className="analytics__field">
              <span>Owner email</span>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </label>
            <button
              type="button"
              className="btn"
              disabled={busy || !apiKey.trim()}
              onClick={() => void createOrg()}
            >
              Create org
            </button>
          </div>
          <div>
            <h3>Spend caps</h3>
            <p className="analytics__note">
              Caps meter pipe rent this UTC month. Soft = headers; hard = 402 on
              MISS. HITs always serve.
            </p>
            <label className="analytics__field">
              <span>Monthly cap USD (0 = off)</span>
              <input
                value={capUsd}
                onChange={(e) => setCapUsd(e.target.value)}
                inputMode="decimal"
              />
            </label>
            <label className="analytics__field">
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
            <label className="analytics__field">
              <span>Per–cost-center JSON</span>
              <input
                value={capOverrides}
                onChange={(e) => setCapOverrides(e.target.value)}
                placeholder='{"ci-prompts": 25}'
              />
            </label>
            <button
              type="button"
              className="btn"
              disabled={busy || !canQuery}
              onClick={() => void saveSpendCaps()}
            >
              Save spend caps
            </button>
          </div>
          <div>
            <h3>Exports</h3>
            <button
              type="button"
              className="btn"
              disabled={busy || !canQuery}
              onClick={() => void downloadMonthCsv()}
            >
              Download {month} CSV
            </button>
            <p className="analytics__note">
              Requires an org-bound key.{" "}
              <Link href="/docs/enterprise-chaos">Enterprise docs</Link>
            </p>
          </div>
        </div>
        {adminLog ? <pre className="org-console__log">{adminLog}</pre> : null}
      </details>
    </div>
  );
}
