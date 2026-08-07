"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { hasOhmSeat } from "@/lib/profileStorage";

/** Soft nudge for returning subscribers who land on checkout again. */
export function ReturningSeatNote() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(hasOhmSeat());
  }, []);

  if (!show) return null;

  return (
    <p className="billing-form__note">
      This browser already has a seat. Open your{" "}
      <Link href="/profile">profile</Link> or{" "}
      <Link href="/keys">API keys</Link> — you do not need to check out again
      to mint another key. On another device?{" "}
      <Link href="/login">Log in</Link> with your key.
    </p>
  );
}
