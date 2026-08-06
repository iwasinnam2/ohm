"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { CopyBlock } from "@/components/CopyBlock";
import { IntegrationBrandBoard } from "@/components/IntegrationBrandBoard";
import { cursorOhmInstallHref } from "@/lib/cursorMcp";

const KEY_PLACEHOLDER = "sk-at-YOUR_KEY";

type HostCard = {
  id: string;
  name: string;
  where: string;
  snippetLabel: string;
  snippet: (key: string) => string;
};

const HOSTS: HostCard[] = [
  {
    id: "cursor",
    name: "Cursor",
    where: "~/.cursor/mcp.json (global) or .cursor/mcp.json (project)",
    snippetLabel: "Cursor mcp.json config",
    snippet: (key) =>
      JSON.stringify(
        {
          mcpServers: {
            ohm: { command: "ohm-mcp", env: { OHM_API_KEY: key } },
          },
        },
        null,
        2,
      ),
  },
  {
    id: "claude-code",
    name: "Claude Code",
    where: "One terminal command",
    snippetLabel: "Claude Code add command",
    snippet: (key) => `claude mcp add ohm --env OHM_API_KEY=${key} -- ohm-mcp`,
  },
  {
    id: "vscode",
    name: "VS Code (Copilot)",
    where: ".vscode/mcp.json in your workspace",
    snippetLabel: "VS Code mcp.json config",
    snippet: (key) =>
      JSON.stringify(
        {
          servers: {
            ohm: { type: "stdio", command: "ohm-mcp", env: { OHM_API_KEY: key } },
          },
        },
        null,
        2,
      ),
  },
  {
    id: "windsurf",
    name: "Windsurf",
    where: "~/.codeium/windsurf/mcp_config.json",
    snippetLabel: "Windsurf mcp_config.json config",
    snippet: (key) =>
      JSON.stringify(
        {
          mcpServers: {
            ohm: { command: "ohm-mcp", env: { OHM_API_KEY: key } },
          },
        },
        null,
        2,
      ),
  },
  {
    id: "zed",
    name: "Zed",
    where: "settings.json (zed: open settings)",
    snippetLabel: "Zed settings.json config",
    snippet: (key) =>
      JSON.stringify(
        {
          context_servers: {
            ohm: { source: "custom", command: "ohm-mcp", args: [], env: { OHM_API_KEY: key } },
          },
        },
        null,
        2,
      ),
  },
];

const SCOPES = [
  {
    name: "Prompts you route through it",
    detail:
      "Chat calls you send via ohm_chat pass through the pipe so identical prompts can replay from cache. Nothing else on your machine is read.",
  },
  {
    name: "Public web pages only",
    detail:
      "ohm_fetch_web fetches public URLs under the compliance policy — robots-gated, PII-redacted, and limited to declared purposes. Ask ohm_policy for the current list.",
  },
  {
    name: "Your usage meters",
    detail:
      "ohm_usage, ohm_savings, ohm_models, and ohm_providers read your own tenant's meters and routing status. Read-only.",
  },
  {
    name: "Keys stay yours",
    detail:
      "BYOK (bring your own keys): provider keys ride the X-Ohm-Upstream-Key header per request and are not stored.",
  },
];

const ROADMAP = [
  {
    name: "Hosted remote MCP",
    detail: "One URL attach (no local install) over streamable HTTP.",
  },
  {
    name: "Slack app",
    detail: "Usage alerts and fetch summaries where your team talks.",
  },
  {
    name: "Automation platforms",
    detail: "Zapier / Make connectors for no-code pipelines.",
  },
];

export function ConnectionsClient() {
  const [apiKey, setApiKey] = useState("");
  const key = apiKey.trim() || KEY_PLACEHOLDER;

  const cursorHref = useMemo(() => {
    const k = apiKey.trim();
    return k ? cursorOhmInstallHref({ apiKey: k }) : null;
  }, [apiKey]);

  return (
    <section className="connect">
      <div className="page-head">
        <h1>Connections</h1>
        <p>
          Interconnectedness and accessibility — withOhm is a cog in your
          workflow machine. Attach once to the tools you already use; every MCP
          host below gets the same seven tools.
        </p>
      </div>

      <IntegrationBrandBoard showIntro={false} />

      <div className="connect__setup" id="setup">
        <p className="connect__step">
          <strong>1.</strong> Install the server:
        </p>
        <CopyBlock text="pip install withohm-mcp" label="install command" compact />
        <p className="connect__step">
          <strong>2.</strong> Paste your key to personalize the configs below
          (or grab a{" "}
          <Link href="/billing/intermediate">$0 Intermediate seat</Link> first):
        </p>
        <label className="connect__key">
          <span>withOhm API key</span>
          <input
            type="password"
            autoComplete="off"
            placeholder="sk-at-…"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </label>
      </div>

      <ul className="connect-grid">
        {HOSTS.map((host) => (
          <li key={host.id} id={host.id} className="connect-card">
            <h2 className="connect-card__name">{host.name}</h2>
            <p className="connect-card__where">{host.where}</p>
            {host.id === "cursor" && cursorHref ? (
              <a className="btn btn--primary connect-card__oneclick" href={cursorHref}>
                Add withOhm to Cursor
              </a>
            ) : null}
            <CopyBlock text={host.snippet(key)} label={host.snippetLabel} />
          </li>
        ))}
      </ul>

      <section
        className="connect-stack"
        id="neon"
        aria-labelledby="connect-neon-title"
      >
        <h2 id="connect-neon-title">On the stack — Neon</h2>
        <div className="connect-card connect-card--stack">
          <h3 className="connect-card__name">Neon</h3>
          <p className="connect-card__where">
            Serverless Postgres — branches, previews, scale-to-zero compute for
            apps and agents.
          </p>
          <p className="connect-stack__body">
            Neon holds application state (and, in beta, a branch-scoped AI
            Gateway). withOhm is middleware governance on mechanical repeats —
            exact-replay tips on the same PR slug, Promote-on-merge, HIT
            meters. Complementary, not competing.
          </p>
          <div className="cta-row">
            <Link className="btn btn--primary" href="/docs/compose-neon">
              Compose with Neon
            </Link>
            <a
              className="btn"
              href="https://neon.tech"
              target="_blank"
              rel="noopener noreferrer"
            >
              neon.tech
            </a>
          </div>
        </div>
      </section>

      <section className="connect-scopes" aria-labelledby="connect-scopes-title">
        <h2 id="connect-scopes-title">What withOhm can access</h2>
        <p className="connect-scopes__lede">
          The connection is deliberately narrow. Once attached, withOhm can
          reach exactly this — nothing more:
        </p>
        <ul className="connect-scopes__list">
          {SCOPES.map((scope) => (
            <li key={scope.name}>
              <strong>{scope.name}.</strong> {scope.detail}
            </li>
          ))}
        </ul>
        <p className="connect-scopes__foot">
          Full detail in <Link href="/docs/security">Security</Link> and{" "}
          <Link href="/docs/legal">Legal &amp; compliance</Link>.
        </p>
      </section>

      <section className="connect-roadmap" aria-labelledby="connect-roadmap-title">
        <h2 id="connect-roadmap-title">Coming to the grid</h2>
        <ul className="connect-roadmap__list">
          {ROADMAP.map((item) => (
            <li key={item.name}>
              <strong>{item.name}.</strong> {item.detail}
            </li>
          ))}
        </ul>
      </section>

      <p className="connect__foot">
        <Link href="/docs/integrations">Full integration guide</Link>
        {" · "}
        <Link href="/docs/commands">Command catalog</Link>
        {" · "}
        <Link href="/docs/optimized-usage">Optimized usage</Link>
      </p>
    </section>
  );
}
