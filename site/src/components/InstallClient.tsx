"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { OhmMark } from "@/components/OhmMark";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";

const SHARE_LINE = "Add withOhm MCP from https://www.withohm.dev/i";

export function InstallClient() {
  const [apiKey, setApiKey] = useState("");
  const [copied, setCopied] = useState(false);

  const href = useMemo(() => {
    const key = apiKey.trim();
    if (!key) return null;
    return cursorOhmInstallHref({ apiKey: key });
  }, [apiKey]);

  async function copyLine() {
    try {
      await navigator.clipboard.writeText(SHARE_LINE);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  return (
    <section className="steal">
      <OhmMark className="steal__mark" />
      <p className="steal__eyebrow">compliant fetch for agents</p>
      <h1 className="steal__title">withOhm</h1>
      <p className="steal__lede">
        One attach. Prompt cache + public URL context in Cursor. BYOK. Paste the
        line to a teammate — that is the product.
      </p>

      <pre className="steal__share" tabIndex={0}>
        {SHARE_LINE}
      </pre>
      <div className="steal__row">
        <button type="button" className="btn btn--ghost" onClick={copyLine}>
          {copied ? "Copied" : "Copy line"}
        </button>
        <Link className="btn btn--primary" href="/billing/intermediate">
          Get a free seat
        </Link>
      </div>

      <label className="steal__key">
        <span>Already have a key? Wire Cursor now</span>
        <input
          type="password"
          autoComplete="off"
          placeholder="sk-at-…"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </label>
      {href ? (
        <a className="btn btn--primary steal__install" href={href}>
          Add withOhm to Cursor
        </a>
      ) : (
        <p className="steal__hint">
          Enter your key for one-click MCP install, or start from{" "}
          <Link href="/billing/intermediate">Intermediate</Link> ($0 membership).
        </p>
      )}

      <p className="steal__foot">
        <Link href="/fetch">Try compliant fetch</Link>
        {" · "}
        <Link href="/templates">Steal the template</Link>
        {" · "}
        <Link href="/bounty">Artifact bounty</Link>
      </p>
    </section>
  );
}
