import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthGateClient } from "@/components/AuthGateClient";

export const metadata: Metadata = {
  title: "Log in",
  description:
    "Log in to withOhm with your sk-at-… API key, or sign up for a $0 Intermediate seat.",
};

function AuthFallback() {
  return (
    <header className="page-head">
      <h1>withOhm</h1>
      <p>Loading…</p>
    </header>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthFallback />}>
      <AuthGateClient initialMode="login" />
    </Suspense>
  );
}
