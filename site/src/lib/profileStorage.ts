import { clearStoredKey, readStoredKey } from "./keyStorage";

export const PROFILE_STORAGE = "ohm_profile";
export const CHECKOUT_FORM_STORAGE = "ohm_checkout_form";

export type OhmProfile = {
  email?: string;
  label?: string;
  activatedAt?: string;
};

export function readCheckoutForm(): { email?: string; label?: string } | null {
  try {
    const raw = localStorage.getItem(CHECKOUT_FORM_STORAGE);
    if (!raw) return null;
    return JSON.parse(raw) as { email?: string; label?: string };
  } catch {
    return null;
  }
}

export function readProfile(): OhmProfile | null {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE);
    if (raw) {
      const parsed = JSON.parse(raw) as OhmProfile;
      if (parsed.email || parsed.label) return parsed;
    }
  } catch {
    /* ignore */
  }
  const form = readCheckoutForm();
  if (form?.email || form?.label) return form;
  return null;
}

export function writeProfile(patch: OhmProfile): void {
  try {
    const prev = readProfile() || {};
    const next: OhmProfile = {
      ...prev,
      ...patch,
      email: (patch.email ?? prev.email)?.trim() || undefined,
      label: (patch.label ?? prev.label)?.trim() || undefined,
    };
    localStorage.setItem(PROFILE_STORAGE, JSON.stringify(next));
  } catch {
    /* ignore */
  }
}

/** Seat is active when a withOhm key is stashed in this browser. */
export function hasOhmSeat(): boolean {
  const key = readStoredKey();
  return Boolean(key && key.startsWith("sk-at-"));
}

export function markSeatActivated(): void {
  writeProfile({ activatedAt: new Date().toISOString() });
}

export function clearSeatLocal(): void {
  clearStoredKey();
  try {
    localStorage.removeItem(PROFILE_STORAGE);
  } catch {
    /* ignore */
  }
}
