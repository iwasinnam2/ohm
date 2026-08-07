"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, startTransition } from "react";
import { BillingCheckoutForm } from "@/components/BillingCheckoutForm";
import { notifySeatChanged } from "@/components/StartOrProfileCta";
import { persistKey } from "@/lib/keyStorage";
import { hasOhmSeat, writeProfile } from "@/lib/profileStorage";

export type AuthMode = "login" | "signup";

type Props = {
  initialMode?: AuthMode;
};

function safeNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/profile";
  return raw;
}

export function AuthGateClient({ initialMode = "login" }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const modeParam = (searchParams.get("mode") || "").toLowerCase();
  const next = safeNext(searchParams.get("next"));

  const [mode, setMode] = useState<AuthMode>(
    modeParam === "signup" || modeParam === "login"
      ? (modeParam as AuthMode)
      : initialMode,
  );
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (hasOhmSeat()) {
      router.replace(next);
      return;
    }
    setReady(true);
  }, [router, next]);

  useEffect(() => {
    if (modeParam === "signup" || modeParam === "login") {
      setMode(modeParam as AuthMode);
    }
  }, [modeParam]);

  function switchMode(nextMode: AuthMode) {
    setError(null);
    setMode(nextMode);
    const params = new URLSearchParams(searchParams.toString());
    params.set("mode", nextMode);
    startTransition(() => {
      router.replace(`/login?${params.toString()}`, { scroll: false });
    });
  }

  async function onLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmed = key.trim();
    if (!trimmed.startsWith("sk-at-")) {
      setError("Keys start with sk-at-…");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/pipe/v1/usage", {
        headers: { Authorization: `Bearer ${trimmed}` },
        cache: "no-store",
      });
      const data = (await res.json().catch(() => ({}))) as {
        detail?: string | { message?: string };
        error?: { message?: string };
        label?: string;
        email?: string;
      };
      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message ||
              data.error?.message ||
              `Could not verify key (HTTP ${res.status})`;
        throw new Error(detail);
      }
      persistKey(trimmed);
      if (data.email || data.label) {
        writeProfile({
          email: typeof data.email === "string" ? data.email : undefined,
          label: typeof data.label === "string" ? data.label : undefined,
        });
      }
      notifySeatChanged();
      router.replace(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  if (!ready) {
    return (
      <header className="page-head">
        <h1>withOhm</h1>
        <p>Checking this browser…</p>
      </header>
    );
  }

  return (
    <div className="auth-gate">
      <header className="auth-gate__brand page-head">
        <p className="auth-gate__eyebrow">withOhm</p>
        <h1>{mode === "login" ? "Log in" : "Sign up"}</h1>
        <p>
          {mode === "login"
            ? "Paste the sk-at-… key from checkout or API keys. This browser keeps the seat — there is no password."
            : "Open a $0 Intermediate seat. Card on file; meters bill usage. Stripe issues your key once."}
        </p>
      </header>

      <div
        className="auth-gate__tabs"
        role="tablist"
        aria-label="Account"
      >
        <button
          type="button"
          role="tab"
          id="auth-tab-login"
          aria-selected={mode === "login"}
          aria-controls="auth-panel-login"
          className={
            mode === "login"
              ? "auth-gate__tab auth-gate__tab--active"
              : "auth-gate__tab"
          }
          onClick={() => switchMode("login")}
        >
          Log in
        </button>
        <button
          type="button"
          role="tab"
          id="auth-tab-signup"
          aria-selected={mode === "signup"}
          aria-controls="auth-panel-signup"
          className={
            mode === "signup"
              ? "auth-gate__tab auth-gate__tab--active"
              : "auth-gate__tab"
          }
          onClick={() => switchMode("signup")}
        >
          Sign up
        </button>
      </div>

      {mode === "login" ? (
        <section
          id="auth-panel-login"
          role="tabpanel"
          aria-labelledby="auth-tab-login"
          className="auth-gate__panel"
        >
          <form className="billing-form auth-gate__form" onSubmit={onLogin}>
            <label className="billing-form__field">
              <span>API key</span>
              <input
                type="password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="sk-at-…"
                autoComplete="current-password"
                spellCheck={false}
                required
                disabled={busy}
              />
            </label>
            {error ? (
              <p className="billing-form__error" role="alert">
                {error}{" "}
                <Link href="/support">Support</Link>
              </p>
            ) : null}
            <button
              type="submit"
              className="btn btn--primary"
              disabled={busy || !key.trim()}
            >
              {busy ? "Verifying…" : "Log in"}
            </button>
            <p className="billing-form__note">
              Lost the secret? Mint another from{" "}
              <Link href="/keys">API keys</Link> while any seat key still works,
              or open a new seat under Sign up. New here?{" "}
              <button
                type="button"
                className="link-quiet"
                onClick={() => switchMode("signup")}
              >
                Create an Intermediate seat
              </button>
              .
            </p>
          </form>
        </section>
      ) : (
        <section
          id="auth-panel-signup"
          role="tabpanel"
          aria-labelledby="auth-tab-signup"
          className="auth-gate__panel"
        >
          <BillingCheckoutForm />
          <p className="billing-form__alt">
            Already have a key?{" "}
            <button
              type="button"
              className="link-quiet"
              onClick={() => switchMode("login")}
            >
              Log in
            </button>
            {" · "}
            <Link href="/subscriptions">Commit tiers</Link>
            {" · "}
            <Link href="/docs/pricing">Meter rates</Link>
          </p>
        </section>
      )}
    </div>
  );
}
