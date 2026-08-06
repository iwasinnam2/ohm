"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { hasOhmSeat } from "@/lib/profileStorage";

type Props = {
  className?: string;
  guestLabel?: string;
  guestHref?: string;
  seatedLabel?: string;
  seatedHref?: string;
};

/**
 * Primary marketing CTA — $0 seat checkout until this browser has a key,
 * then Profile.
 */
export function StartOrProfileCta({
  className = "btn btn--primary",
  guestLabel = "Start now — $0 seat",
  guestHref = "/billing/intermediate",
  seatedLabel = "Profile",
  seatedHref = "/profile",
}: Props) {
  const [seated, setSeated] = useState(false);

  useEffect(() => {
    function sync() {
      setSeated(hasOhmSeat());
    }
    sync();
    window.addEventListener("storage", sync);
    window.addEventListener("ohm-seat-changed", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("ohm-seat-changed", sync);
    };
  }, []);

  return (
    <Link
      href={seated ? seatedHref : guestHref}
      className={className}
    >
      {seated ? seatedLabel : guestLabel}
    </Link>
  );
}

export function notifySeatChanged(): void {
  try {
    window.dispatchEvent(new Event("ohm-seat-changed"));
  } catch {
    /* ignore */
  }
}
