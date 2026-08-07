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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    const path = nextMode === "signup" ? "/signup" : "/login";
    startTransition(() => {
      router.replace(`${path}?${params.toString()}`, { scroll: false });
    });
  }

  async function onLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const em = email.trim();
    if (!em || !password) {
      setError("Email and password are required.");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/pipe/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: em, password }),
        cache: "no-store",
      });
      const data = (await res.json().catch(() => ({}))) as {
        detail?: string | { message?: string };
        error?: { message?: string };
        api_key?: string;
        tenant?: { email?: string; label?: string };
      };
      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message ||
              data.error?.message ||
              `Login failed (HTTP ${res.status})`;
        throw new Error(detail);
      }
      const key = data.api_key;
      if (!key?.startsWith("sk-at-")) {
        throw new Error("Login succeeded but no seat key was returned.");
      }
      persistKey(key);
      writeProfile({
        email: data.tenant?.email || em,
        label: data.tenant?.label,
      });
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
        <h1>{mode === "login" ? "Log in" : "Create account"}</h1>
        <p>
          {mode === "login"
            ? "Use the email and password you chose at checkout. Your Intermediate seat key is restored in this browser."
            : "Open a $0 Intermediate seat. Choose a password now — you will log in with email, not by pasting a key."}
        </p>
      </header>

      <div className="auth-gate__tabs" role="tablist" aria-label="Account">
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
          Create account
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
              <span>Email</span>
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
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
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
              disabled={busy || !email.trim() || !password}
            >
              {busy ? "Signing in…" : "Log in"}
            </button>
            <p className="billing-form__note">
              New here?{" "}
              <button
                type="button"
                className="link-quiet"
                onClick={() => switchMode("signup")}
              >
                Create an account
              </button>
              . Pipe keys still live under{" "}
              <Link href="/keys">API keys</Link> after you sign in.
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
            Already subscribed?{" "}
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
