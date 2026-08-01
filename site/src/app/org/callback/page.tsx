"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

const API = (
  process.env.NEXT_PUBLIC_OHM_API_URL || "https://api.withohm.dev"
).replace(/\/$/, "");

function CallbackInner() {
  const params = useSearchParams();
  const [msg, setMsg] = useState("Completing SSO…");

  useEffect(() => {
    const code = params.get("code");
    const orgId = params.get("org_id") || "";
    if (!code) {
      setMsg("Missing OIDC code. Start from /org or your IdP.");
      return;
    }
    fetch(`${API}/v1/org/sso/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, org_id: orgId }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          setMsg(`SSO failed: ${JSON.stringify(data)}`);
          return;
        }
        if (typeof window !== "undefined" && data.session_token) {
          sessionStorage.setItem("ohm_session", data.session_token);
        }
        setMsg(
          `Signed in as ${data.email} (org ${data.org_id}). Session stored — open /org and paste X-Ohm-Session if needed.`
        );
      })
      .catch((e) => setMsg(String(e)));
  }, [params]);

  return <p className="agent-shell__meta">{msg}</p>;
}

export default function OrgCallbackPage() {
  return (
    <>
      <header className="page-head">
        <h1>SSO callback</h1>
      </header>
      <Suspense fallback={<p>Loading…</p>}>
        <CallbackInner />
      </Suspense>
    </>
  );
}
