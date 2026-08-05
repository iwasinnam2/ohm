"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

export function FetchToyClient() {
  const search = useSearchParams();
  const [url, setUrl] = useState("");
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const run = useCallback(async (target: string) => {
    const u = target.trim();
    if (!u) return;
    setBusy(true);
    setError(null);
    setMarkdown(null);
    try {
      const res = await fetch(
        `/api/public-fetch?url=${encodeURIComponent(u)}`,
      );
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || `Fetch failed (${res.status})`);
      }
      setMarkdown(String(data.markdown || ""));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    const q = search.get("url");
    if (q) {
      setUrl(q);
      void run(q);
    }
  }, [search, run]);

  async function copyOut() {
    if (!markdown) return;
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  return (
    <section className="steal steal--fetch">
      <p className="steal__eyebrow">public fetch demo</p>
      <h1 className="steal__title">Fetch toy</h1>
      <p className="steal__lede">
        Paste a public URL. Get a markdown preview (demo HTML strip — not the
        full robots/purpose-gated Ohm pipe). Soft rate limit. Full Cursor pipe:{" "}
        <Link href="/i">www.withohm.dev/i</Link>
      </p>

      <form
        className="steal__form"
        onSubmit={(e) => {
          e.preventDefault();
          const next = new URL(window.location.href);
          next.searchParams.set("url", url.trim());
          window.history.replaceState({}, "", next.toString());
          void run(url);
        }}
      >
        <input
          type="url"
          required
          aria-label="Public URL to fetch"
          placeholder="https://docs.example.com/…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={busy}
        />
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? "Fetching…" : "Fetch"}
        </button>
      </form>

      {error ? (
        <p className="billing-form__error" role="alert">
          {error}
        </p>
      ) : null}

      {markdown ? (
        <div className="steal__out">
          <div className="steal__out-bar">
            <span>Shareable output</span>
            <button
              type="button"
              className="link-quiet"
              aria-label="Copy fetched markdown"
              onClick={copyOut}
            >
              {copied ? "Copied" : "Copy markdown"}
            </button>
            <span role="status" className="visually-hidden">
              {copied ? "Markdown copied to clipboard" : ""}
            </span>
          </div>
          <pre className="steal__markdown" tabIndex={0} aria-label="Fetched markdown">
            {markdown}
          </pre>
          <p className="steal__hint">
            Want this inside Cursor?{" "}
            <Link href="/i">Add withOhm MCP from https://www.withohm.dev/i</Link>
          </p>
        </div>
      ) : null}
    </section>
  );
}
