"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { keyPrefix, maskKey, readStoredKey } from "@/lib/keyStorage";
import {
  clearSeatLocal,
  hasOhmSeat,
  readProfile,
  type OhmProfile,
} from "@/lib/profileStorage";
import { notifySeatChanged } from "@/components/StartOrProfileCta";

export default function ProfilePage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [seated, setSeated] = useState(false);
  const [profile, setProfile] = useState<OhmProfile | null>(null);
  const [key, setKey] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);

  useEffect(() => {
    const has = hasOhmSeat();
    setSeated(has);
    setProfile(readProfile());
    setKey(readStoredKey());
    setReady(true);
    if (!has) {
      router.replace("/login?next=/profile");
    }
  }, [router]);

  function signOut() {
    clearSeatLocal();
    notifySeatChanged();
    router.push("/login");
  }

  if (!ready || !seated) {
    return (
      <header className="page-head">
        <h1>Profile</h1>
        <p>Loading your seat…</p>
      </header>
    );
  }

  return (
    <>
      <header className="page-head">
        <h1>Profile</h1>
        <p>
          Your Intermediate seat in this browser. Keys stay local — we never
          re-show a secret after first reveal on the success page.
        </p>
      </header>

      <dl className="profile-card">
        <div>
          <dt>Organisation</dt>
          <dd>{profile?.label || "—"}</dd>
        </div>
        <div>
          <dt>Work email</dt>
          <dd>{profile?.email || "—"}</dd>
        </div>
        <div>
          <dt>Plan</dt>
          <dd>$0 Intermediate · meters · BYOK</dd>
        </div>
        <div>
          <dt>API key</dt>
          <dd>
            <code>
              {key
                ? showSecret
                  ? key
                  : maskKey(key)
                : "—"}
            </code>
            {key ? (
              <>
                {" "}
                <button
                  type="button"
                  className="link-quiet"
                  onClick={() => setShowSecret((v) => !v)}
                >
                  {showSecret ? "Hide" : "Reveal"}
                </button>
                <span className="profile-card__hint">
                  {" "}
                  ({keyPrefix(key)})
                </span>
              </>
            ) : null}
          </dd>
        </div>
        {profile?.activatedAt ? (
          <div>
            <dt>Activated</dt>
            <dd>{new Date(profile.activatedAt).toLocaleString()}</dd>
          </div>
        ) : null}
      </dl>

      <div className="cta-row">
        <Link href="/keys" className="btn btn--primary">
          Manage API keys
        </Link>
        <Link href="/org" className="btn">
          Analytics
        </Link>
        <Link href="/workbench" className="btn">
          Agent Shell
        </Link>
        <Link href="/connections" className="btn">
          Connect tools
        </Link>
      </div>

      <p className="status-foot">
        <button type="button" className="link-quiet" onClick={signOut}>
          Clear this browser seat
        </button>
        {" · "}
        <Link href="/support">Support</Link>
        {" · "}
        <Link href="/billing/intermediate">Checkout again</Link>
      </p>
    </>
  );
}
