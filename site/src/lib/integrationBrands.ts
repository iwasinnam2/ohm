/** Brand board — interconnected tools people already trust. */

export type BrandTile = {
  id: string;
  name: string;
  kind: "agent" | "pipe" | "surface";
  blurb: string;
  /** Official product site (trust signal). */
  href: string;
  /** In-app deep link when we have a setup surface. */
  setupHref?: string;
};

export const INTEGRATION_BRANDS: BrandTile[] = [
  {
    id: "cursor",
    name: "Cursor",
    kind: "agent",
    blurb: "MCP one-click + mcp.json",
    href: "https://cursor.com",
    setupHref: "/connections#cursor",
  },
  {
    id: "claude-code",
    name: "Claude Code",
    kind: "agent",
    blurb: "Terminal MCP attach",
    href: "https://docs.anthropic.com/en/docs/claude-code",
    setupHref: "/connections#claude-code",
  },
  {
    id: "vscode",
    name: "VS Code",
    kind: "agent",
    blurb: "Copilot agent MCP",
    href: "https://code.visualstudio.com",
    setupHref: "/connections#vscode",
  },
  {
    id: "windsurf",
    name: "Windsurf",
    kind: "agent",
    blurb: "Codeium MCP config",
    href: "https://windsurf.com",
    setupHref: "/connections#windsurf",
  },
  {
    id: "zed",
    name: "Zed",
    kind: "agent",
    blurb: "Context servers",
    href: "https://zed.dev",
    setupHref: "/connections#zed",
  },
  {
    id: "openai",
    name: "OpenAI",
    kind: "pipe",
    blurb: "Compatible /v1 + BYOK",
    href: "https://platform.openai.com",
    setupHref: "/docs/quickstart",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    kind: "pipe",
    blurb: "BYOK on the pipe",
    href: "https://www.anthropic.com",
    setupHref: "/docs/quickstart",
  },
  {
    id: "mcp",
    name: "MCP",
    kind: "pipe",
    blurb: "Open agent protocol",
    href: "https://modelcontextprotocol.io",
    setupHref: "/docs/commands",
  },
  {
    id: "stripe",
    name: "Stripe",
    kind: "pipe",
    blurb: "Seats + meters",
    href: "https://stripe.com",
    setupHref: "/docs/pricing",
  },
  {
    id: "redis",
    name: "Redis",
    kind: "pipe",
    blurb: "Exact-match replay",
    href: "https://redis.io",
    setupHref: "/docs/optimized-usage",
  },
  {
    id: "shell",
    name: "Agent Shell",
    kind: "surface",
    blurb: "Ohm workbench",
    href: "/workbench",
    setupHref: "/workbench",
  },
  {
    id: "org",
    name: "Org console",
    kind: "surface",
    blurb: "Ledger + policy",
    href: "/org",
    setupHref: "/org",
  },
];

export const BRAND_KIND_LABEL: Record<BrandTile["kind"], string> = {
  agent: "Coding agents",
  pipe: "On the pipe",
  surface: "withOhm surfaces",
};
