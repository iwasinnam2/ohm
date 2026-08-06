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
        Interconnectedness and accessibility — Agent Shell, any OpenAI SDK, or
        MCP attach for Cursor and friends. Same pipe either way.
      </p>

      <div className="steal__row">
        <Link className="btn btn--primary" href="/workbench">
          Open Agent Shell
        </Link>
        <Link className="btn" href="/docs/integrations">
          Integrations board
        </Link>
        <Link className="btn" href="/billing/intermediate">
          Get a $0 seat
        </Link>
      </div>

      <p className="steal__hint">OpenAI-compatible base URL</p>
      <CopyBlock text={BASE_URL_LINE} label="base_URL" compact />

      <CopyBlock text={SHARE_LINE} label="share line" compact />

      <label className="steal__key">
        <span>Wire Cursor with your key</span>
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
          <Link href="/billing/intermediate">Intermediate</Link>.
        </p>
      )}

      <p className="steal__foot">
        <Link href="/docs/quickstart">Quickstart</Link>
        {" · "}
        <Link href="/connections">All hosts</Link>
        {" · "}
        <Link href="/org">Analytics</Link>
        {" · "}
        <Link href="/docs/pricing">Pricing</Link>
      </p>
    </section>
  );
}
