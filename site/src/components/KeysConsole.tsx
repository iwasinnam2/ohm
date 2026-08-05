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

type KeyMeta = {
  plan?: string;
  status?: string;
  billing_paid?: boolean;
  usage_unlocked?: boolean;
};

export function KeysConsole() {
  const [secret, setSecret] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [copied, setCopied] = useState(false);
  const [paste, setPaste] = useState("");
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

  useEffect(() => {
    if (secret) {
      void verify(secret);
    } else {
      setMeta(null);
      setVerifiedAt(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- verify on secret change only
  }, [secret]);

  async function copyKey() {
    if (!secret) return;
    try {
      await navigator.clipboard.writeText(secret);
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
    setRevealed(false);
  }

  function onClearBrowser() {
    clearStoredKey();
    setSecret(null);
    setMeta(null);
    setRevealed(false);
    setVerifiedAt(null);
    setError(null);
  }

  return (
    <div className="keys-console">
      <header className="page-head">
        <p className="keys-console__eyebrow">Account</p>
        <h1>API keys</h1>
        <p>
          Secret keys authenticate every request to{" "}
          <code>api.withohm.dev</code>. We store only a hash — the full secret
          is shown once at issue. Keep it in a password manager; this page
          recovers what this browser still holds, or lets you paste one back
          in.
        </p>
      </header>

      <section className="keys-console__panel" aria-labelledby="keys-table-title">
        <div className="keys-console__panel-head">
          <h2 id="keys-table-title">Your keys</h2>
          <Link href="/billing/intermediate" className="btn btn--primary">
            Create new key
          </Link>
        </div>

        {secret ? (
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
                <tr>
                  <td>
                    <span className="keys-table__name">Default</span>
                    <span className="keys-table__hint">
                      prefix {keyPrefix(secret)}
                    </span>
                  </td>
                  <td>
                    <code className="keys-table__secret">
                      {revealed ? secret : maskKey(secret)}
                    </code>
                  </td>
                  <td>{meta?.plan ?? (busy ? "…" : "—")}</td>
                  <td>
                    <span
                      className={
                        meta?.status === "active"
                          ? "keys-pill keys-pill--ok"
                          : "keys-pill"
                      }
                    >
                      {meta?.status ?? (busy ? "checking" : "unknown")}
                    </span>
                  </td>
                  <td>
                    <div className="keys-table__actions">
                      <button
                        type="button"
                        className="btn"
                        onClick={() => setRevealed((v) => !v)}
                      >
                        {revealed ? "Hide" : "Reveal"}
                      </button>
                      <button
                        type="button"
                        className="btn btn--primary"
                        onClick={copyKey}
                      >
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            {verifiedAt ? (
              <p className="keys-console__meta">
                Verified against <code>/v1/usage</code>
                {meta?.billing_paid != null
                  ? ` · billing_paid=${String(meta.billing_paid)}`
                  : ""}
                {meta?.usage_unlocked != null
                  ? ` · usage_unlocked=${String(meta.usage_unlocked)}`
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
              <Link href="/connections" className="link-quiet">
                Connections
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
        ) : (
          <div className="keys-console__empty">
            <p>
              No key found in this browser. If you copied it at checkout, paste
              it below. Otherwise mint a new Intermediate seat — the previous
              secret cannot be reconstructed from our servers.
            </p>
            <div className="cta-row">
              <Link href="/billing/intermediate" className="btn btn--primary">
                Create Intermediate key
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
          Paste a secret you already saved. We verify it, then stash it in this
          browser for demo, Shell, and Connections.
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
            Issued once at{" "}
            <Link href="/billing/intermediate">Intermediate checkout</Link> (or
            by an operator). Lost secrets are not recoverable — create a new
            key.
          </li>
          <li>
            Provider keys (OpenAI / Anthropic) are BYOK via{" "}
            <code>X-Ohm-Upstream-Key</code> — never stored by withOhm.
          </li>
        </ul>
      </aside>
    </div>
  );
}
