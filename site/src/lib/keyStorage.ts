/** Browser-side withOhm key stash — same keys as checkout / success. */

export const KEY_STORAGE = "ohm_api_key";
export const KEY_STORAGE_LOCAL = "ohm_api_key_backup";

export function readStoredKey(): string | null {
  try {
    const fromSession = sessionStorage.getItem(KEY_STORAGE);
    if (fromSession) return fromSession;
  } catch {
    /* ignore */
  }
  try {
    return localStorage.getItem(KEY_STORAGE_LOCAL);
  } catch {
    return null;
  }
}

export function persistKey(key: string): void {
  try {
    sessionStorage.setItem(KEY_STORAGE, key);
  } catch {
    /* ignore */
  }
  try {
    localStorage.setItem(KEY_STORAGE_LOCAL, key);
  } catch {
    /* ignore */
  }
}

export function clearStoredKey(): void {
  try {
    sessionStorage.removeItem(KEY_STORAGE);
  } catch {
    /* ignore */
  }
  try {
    localStorage.removeItem(KEY_STORAGE_LOCAL);
  } catch {
    /* ignore */
  }
}

export function keyPrefix(key: string): string {
  const k = key.trim();
  if (k.length <= 12) return k;
  return `${k.slice(0, 10)}…`;
}

export function maskKey(key: string): string {
  const k = key.trim();
  if (k.length <= 14) return "•".repeat(Math.min(k.length, 24));
  return `${k.slice(0, 10)}${"•".repeat(18)}${k.slice(-4)}`;
}
