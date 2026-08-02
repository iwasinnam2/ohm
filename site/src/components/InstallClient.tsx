"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { CopyBlock } from "@/components/CopyBlock";
import { OhmMark } from "@/components/OhmMark";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";

const SHARE_LINE = "Add withOhm from https://www.withohm.dev/i";
const BASE_URL_LINE = "https://api.withohm.dev/v1";

export function InstallClient() {
  const [apiKey, setApiKey] = useState("");

  const href = useMemo(() => {
    const key = apiKey.trim();
    if (!key) return null;
    return cursorOhmInstallHref({ apiKey: key });
  }, [apiKey]);

  return (
    <section className="steal">
      <OhmMark className="steal__mark" />
      <p className="steal__eyebrow">Install withOhm</p>
      <h1 className="steal__title">withOhm</h1>
      <p className="steal__lede">
        Primary path: Agent Shell or any OpenAI SDK against one base URL.
        MCP attach (Cursor and friends) is compatibility — not required.
      </p>

      <div className="steal__row">
        <Link className="btn btn--primary" href="/workbench">
          Open Agent Shell
        </Link>
        <Link className="btn" href="/demo">
          60s miss→HIT demo
        </Link>
        <Link className="btn" href="/billing/intermediate">
          Get a $0 seat
        </Link>
      </div>

      <p className="steal__hint">OpenAI-compatible base URL</p>
      <CopyBlock text={BASE_URL_LINE} label="base_URL" compact />

      <CopyBlock text={SHARE_LINE} label="share line" compact />

      <label className="steal__key">
        <span>Optional — wire Cursor MCP with your key</span>
        <input
          type="password"
          autoComplete="off"
          placeholder="sk-at-…"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </label>
      {href ? (
        <a className="btn steal__install" href={href}>
          Add MCP to Cursor (compatibility)
        </a>
      ) : (
        <p className="steal__hint">
          Prefer the Shell. MCP is optional — enter a key only if you want
          one-click Cursor attach.
        </p>
      )}

      <p className="steal__foot">
        <Link href="/docs/quickstart">Quickstart (base_URL)</Link>
        {" · "}
        <Link href="/org">Org console</Link>
        {" · "}
        <Link href="/connections">Other MCP hosts</Link>
        {" · "}
        <Link href="/docs/pricing">Pricing</Link>
      </p>
    </section>
  );
}
