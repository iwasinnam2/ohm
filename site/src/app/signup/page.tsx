import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthGateClient } from "@/components/AuthGateClient";

export const metadata: Metadata = {
  title: "Sign up",
  description:
    "Sign up for withOhm — $0 Intermediate seat, card on file, metered pipe rent. Checkout issues your sk-at-… key once.",
};

function AuthFallback() {
  return (
    <header className="page-head">
      <h1>withOhm</h1>
      <p>Loading…</p>
    </header>
  );
}

/** Classic sign-up entry — same gate as /login with Sign up selected. */
export default function SignupPage() {
  return (
    <Suspense fallback={<AuthFallback />}>
      <AuthGateClient initialMode="signup" />
    </Suspense>
  );
}
