"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  clearStoredKey,
  keyPrefix,
  maskKey,
  persistKey,
  readStoredKey,
} from "@/lib/keyStorage";

const API = "/api/pipe";

type KeyRow = {
  tenant_id: string;
  plan?: string;
  status?: string;
  key_prefix?: string;
  label?: string | null;
  billing_paid?: boolean;
  created_at?: number;
};

type KeyMeta = {
  plan?: string;
  status?: string;
  billing_paid?: boolean;
  usage_unlocked?: boolean;
};

export function KeysConsole() {
  const [secret, setSecret] = useState<string | null>(null);
  const [keys, setKeys] = useState<KeyRow[]>([]);
  const [revealedId, setRevealedId] = useState<string | null>(null);
  const [freshSecret, setFreshSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [paste, setPaste] = useState("");
  const [label, setLabel] = useState("");
  const [meta, setMeta] = useState<KeyMeta | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifiedAt, setVerifiedAt] = useState<string | null>(null);

  const refreshFromBrowser = useCallback(() => {
    setSecret(readStoredKey());
  }, []);

  useEffect(() => {
    refreshFromBrowser();
  }, [refreshFromBrowser]);

  async function verify(key: string): Promise<boolean> {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/v1/usage`, {
        headers: { Authorization: `Bearer ${key}` },
        cache: "no-store",
      });
      const data = (await res.json().catch(() => ({}))) as KeyMeta & {
        detail?: string | { message?: string };
        error?: { message?: string };
      };
      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message ||
              data.error?.message ||
              `HTTP ${res.status}`;
        throw new Error(detail);
      }
      setMeta({
        plan: data.plan,
        status: data.status,
        billing_paid: data.billing_paid,
        usage_unlocked: data.usage_unlocked,
      });
      setVerifiedAt(new Date().toISOString());
      return true;
    } catch (err) {
      setMeta(null);
      setVerifiedAt(null);
      setError(err instanceof Error ? err.message : String(err));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function loadAccountKeys(key: string) {
    try {
      const res = await fetch(`${API}/v1/account/keys`, {
        headers: { Authorization: `Bearer ${key}` },
        cache: "no-store",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        // Pre-subscribe or legacy — fall back to local-only row.
        setKeys([]);
        return;
      }
      setKeys(Array.isArray(data.keys) ? data.keys : []);
    } catch {
      setKeys([]);
    }
  }

  useEffect(() => {
    if (secret) {
      void (async () => {
        const ok = await verify(secret);
        if (ok) await loadAccountKeys(secret);
      })();
    } else {
      setMeta(null);
      setVerifiedAt(null);
      setKeys([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- verify on secret change only
  }, [secret]);

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setError("Clipboard blocked — select the key and copy manually.");
    }
  }

  async function onRestore(e: React.FormEvent) {
    e.preventDefault();
    const key = paste.trim();
    if (!key.startsWith("sk-at-")) {
      setError("Keys start with sk-at-…");
      return;
    }
    const ok = await verify(key);
    if (!ok) return;
    persistKey(key);
    setSecret(key);
    setPaste("");
    setFreshSecret(null);
    setRevealedId(null);
  }

  async function onMint(e: React.FormEvent) {
    e.preventDefault();
    if (!secret) return;
    setBusy(true);
    setError(null);
    setFreshSecret(null);
    try {
      const res = await fetch(`${API}/v1/account/keys`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${secret}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ label: label.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data?.detail;
        throw new Error(
          typeof detail === "string"
            ? detail
            : detail?.message || data?.error?.message || `HTTP ${res.status}`,
        );
      }
      const minted = data.api_key as string;
      if (!minted) throw new Error("API key missing from response");
      setFreshSecret(minted);
      persistKey(minted);
      setSecret(minted);
      setLabel("");
      await loadAccountKeys(minted);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(tenantId: string) {
    if (!secret) return;
    if (
      !window.confirm(
        "Revoke this key permanently? Requests with that secret will fail.",
      )
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/v1/account/keys/${encodeURIComponent(tenantId)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${secret}` },
        },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data?.detail;
        throw new Error(
          typeof detail === "string"
            ? detail
            : detail?.message || data?.error?.message || `HTTP ${res.status}`,
        );
      }
      const deletedSelf = keys.find(
        (k) =>
          k.tenant_id === tenantId &&
          secret.startsWith(k.key_prefix || "___"),
      );
      // Prefix match is imperfect; if usage fails after delete, clear browser.
      await loadAccountKeys(secret);
      const stillOk = await verify(secret);
      if (!stillOk || deletedSelf) {
        clearStoredKey();
        setSecret(null);
        setKeys([]);
        setFreshSecret(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function onClearBrowser() {
    clearStoredKey();
    setSecret(null);
    setMeta(null);
    setKeys([]);
    setFreshSecret(null);
    setRevealedId(null);
    setVerifiedAt(null);
    setError(null);
  }

  const localPrefix = secret ? keyPrefix(secret) : "";
  const rows: KeyRow[] =
    keys.length > 0
      ? keys
      : secret
        ? [
            {
              tenant_id: "local",
              label: "This browser",
              key_prefix: localPrefix.replace(/…$/, ""),
              plan: meta?.plan,
              status: meta?.status,
            },
          ]
        : [];

  return (
    <div className="keys-console">
      <header className="page-head">
        <p className="keys-console__eyebrow">Account</p>
        <h1>API keys</h1>
        <p>
          Secret keys authenticate every request to{" "}
          <code>api.withohm.dev</code>. We store only a hash — the full secret
          is shown once at issue. Subscribers mint and revoke keys here without
          checking out again.
        </p>
      </header>

      <section className="keys-console__panel" aria-labelledby="keys-table-title">
        <div className="keys-console__panel-head">
          <h2 id="keys-table-title">Your keys</h2>
        </div>

        {secret ? (
          <>
            <form className="billing-form" onSubmit={onMint}>
              <label className="billing-form__field">
                <span>New key label (optional)</span>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="ci-bot"
                  disabled={busy}
                />
              </label>
              <button
                type="submit"
                className="btn btn--primary"
                disabled={busy}
              >
                {busy ? "Working…" : "Create key"}
              </button>
            </form>

            {freshSecret ? (
              <div className="billing-form__key-panel" role="status">
                <p className="keys-console__lede">
                  New secret — copy now; it will not be shown again.
                </p>
                <code className="billing-form__key-code">{freshSecret}</code>
                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => copyText(freshSecret)}
                >
                  {copied ? "Copied" : "Copy key"}
                </button>
              </div>
            ) : null}

            <div className="keys-table-wrap">
              <table className="keys-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Key</th>
                    <th scope="col">Plan</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const isBrowser =
                      !!secret &&
                      !!row.key_prefix &&
                      secret.startsWith(row.key_prefix);
                    const showFull =
                      revealedId === row.tenant_id && isBrowser && secret;
                    return (
                      <tr key={row.tenant_id}>
                        <td>
                          <span className="keys-table__name">
                            {row.label || "Key"}
                          </span>
                          <span className="keys-table__hint">
                            prefix {row.key_prefix || "—"}
                          </span>
                        </td>
                        <td>
                          <code className="keys-table__secret">
                            {showFull
                              ? secret
                              : row.key_prefix
                                ? `${row.key_prefix}${"•".repeat(18)}`
                                : maskKey(secret || "")}
                          </code>
                        </td>
                        <td>{row.plan ?? (busy ? "…" : "—")}</td>
                        <td>
                          <span
                            className={
                              row.status === "active"
                                ? "keys-pill keys-pill--ok"
                                : "keys-pill"
                            }
                          >
                            {row.status ?? (busy ? "checking" : "unknown")}
                          </span>
                        </td>
                        <td>
                          <div className="keys-table__actions">
                            {isBrowser ? (
                              <>
                                <button
                                  type="button"
                                  className="btn"
                                  onClick={() =>
                                    setRevealedId((id) =>
                                      id === row.tenant_id
                                        ? null
                                        : row.tenant_id,
                                    )
                                  }
                                >
                                  {showFull ? "Hide" : "Reveal"}
                                </button>
                                <button
                                  type="button"
                                  className="btn btn--primary"
                                  onClick={() => copyText(secret)}
                                >
                                  {copied ? "Copied" : "Copy"}
                                </button>
                              </>
                            ) : null}
                            {row.tenant_id !== "local" ? (
                              <button
                                type="button"
                                className="link-quiet keys-console__danger"
                                onClick={() => onDelete(row.tenant_id)}
                                disabled={busy}
                              >
                                Delete
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {verifiedAt ? (
                <p className="keys-console__meta">
                  Verified against <code>/v1/usage</code>
                  {meta?.billing_paid != null
                    ? ` · billing_paid=${String(meta.billing_paid)}`
                    : ""}
                  .
                </p>
              ) : null}
              <div className="cta-row">
                <Link href="/demo" className="btn btn--primary">
                  Run 60s demo
                </Link>
                <Link href="/workbench" className="btn">
                  Open Agent Shell
                </Link>
                <button
                  type="button"
                  className="link-quiet keys-console__danger"
                  onClick={onClearBrowser}
                >
                  Clear from this browser
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="keys-console__empty">
            <p>
              No key in this browser. After Intermediate checkout, the success
              page reveals your first secret. Paste a saved key below to manage
              the account, or subscribe once to start.
            </p>
            <div className="cta-row">
              <Link href="/signup" className="btn btn--primary">
                Sign up (first key)
              </Link>
              <Link href="/login" className="link-quiet">
                Log in
              </Link>
              <Link href="/support" className="link-quiet">
                Support
              </Link>
            </div>
          </div>
        )}
      </section>

      <section className="keys-console__panel" aria-labelledby="keys-restore-title">
        <h2 id="keys-restore-title">Restore a key</h2>
        <p className="keys-console__lede">
          Paste a secret you already saved — or use{" "}
          <Link href="/login">Log in</Link>. We verify it, then stash it in this
          browser so you can mint and delete keys without re-entering billing
          details.
        </p>
        <form className="billing-form" onSubmit={onRestore}>
          <label className="billing-form__field">
            <span>Secret key</span>
            <input
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="sk-at-…"
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
            />
          </label>
          {error ? (
            <p className="billing-form__error" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            className="btn btn--primary"
            disabled={busy || paste.trim().length < 10}
          >
            {busy ? "Verifying…" : "Verify and save"}
          </button>
        </form>
      </section>

      <aside className="keys-console__aside">
        <h2>How keys work</h2>
        <ul>
          <li>
            Format <code>sk-at-…</code> — send as{" "}
            <code>Authorization: Bearer …</code>.
          </li>
          <li>
            First key is issued only after Stripe Checkout succeeds. Later keys
            are created here with Create key — no re-checkout.
          </li>
          <li>
            Delete revokes the secret immediately. Lost secrets cannot be
            reconstructed — mint a replacement.
          </li>
        </ul>
      </aside>
    </div>
  );
}
