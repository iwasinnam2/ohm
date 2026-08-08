/** Brand board — interconnected tools with one-click authorize/integrate. */

export type BrandTile = {
  id: string;
  name: string;
  kind: "agent" | "pipe" | "surface";
  blurb: string;
  /** Official product site (trust signal). */
  href: string;
  /** One-click authorize / integrate URL (OAuth or marketplace deep link). */
  authorizeHref: string;
  /** Optional letter mark when no SVG logo ships yet. */
  mark: string;
  /** CSS accent for the mark tile. */
  markColor: string;
};

export const INTEGRATION_BRANDS: BrandTile[] = [
  {
    id: "cursor",
    name: "Cursor",
    kind: "agent",
    blurb: "MCP marketplace attach",
    href: "https://cursor.com",
    authorizeHref:
      "https://cursor.com/install-mcp?name=withOhm&config=eyJ1cmwiOiJodHRwczovL21jcC53aXRob2htLmRldi9tY3AifQ",
    mark: "Cu",
    markColor: "#000000",
  },
  {
    id: "claude-code",
    name: "Claude Code",
    kind: "agent",
    blurb: "Terminal MCP authorize",
    href: "https://docs.anthropic.com/en/docs/claude-code",
    authorizeHref: "/connections#claude-code",
    mark: "Cl",
    markColor: "#D97757",
  },
  {
    id: "vscode",
    name: "VS Code",
    kind: "agent",
    blurb: "Copilot agent MCP",
    href: "https://code.visualstudio.com",
    authorizeHref: "/connections#vscode",
    mark: "VS",
    markColor: "#0078D4",
  },
  {
    id: "windsurf",
    name: "Windsurf",
    kind: "agent",
    blurb: "Codeium MCP config",
    href: "https://windsurf.com",
    authorizeHref: "/connections#windsurf",
    mark: "Wi",
    markColor: "#0EA5E9",
  },
  {
    id: "zed",
    name: "Zed",
    kind: "agent",
    blurb: "Context servers",
    href: "https://zed.dev",
    authorizeHref: "/connections#zed",
    mark: "Ze",
    markColor: "#0847F7",
  },
  {
    id: "jetbrains",
    name: "JetBrains",
    kind: "agent",
    blurb: "AI Assistant MCP plugin",
    href: "https://www.jetbrains.com/ai/",
    authorizeHref: "/docs/integrations",
    mark: "JB",
    markColor: "#FE315D",
  },
  {
    id: "openai",
    name: "OpenAI",
    kind: "pipe",
    blurb: "Compatible /v1 + BYOK",
    href: "https://platform.openai.com",
    authorizeHref: "https://platform.openai.com/api-keys",
    mark: "OAI",
    markColor: "#10A37F",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    kind: "pipe",
    blurb: "BYOK on the pipe",
    href: "https://console.anthropic.com",
    authorizeHref: "https://console.anthropic.com/settings/keys",
    mark: "An",
    markColor: "#D4A27F",
  },
  {
    id: "mcp",
    name: "MCP",
    kind: "pipe",
    blurb: "Open agent protocol",
    href: "https://modelcontextprotocol.io",
    authorizeHref: "/docs/commands",
    mark: "MCP",
    markColor: "#6B5CE7",
  },
  {
    id: "stripe",
    name: "Stripe",
    kind: "pipe",
    blurb: "Seats + meters",
    href: "https://stripe.com",
    authorizeHref: "https://dashboard.stripe.com/apikeys",
    mark: "St",
    markColor: "#635BFF",
  },
  {
    id: "redis",
    name: "Redis",
    kind: "pipe",
    blurb: "Exact-match replay",
    href: "https://redis.io",
    authorizeHref: "https://redis.io/cloud/",
    mark: "Re",
    markColor: "#DC382D",
  },
  {
    id: "shell",
    name: "Agent Shell",
    kind: "surface",
    blurb: "Ohm workbench",
    href: "/workbench",
    authorizeHref: "/workbench",
    mark: "Ω",
    markColor: "#7C3AED",
  },
  {
    id: "org",
    name: "Analytics",
    kind: "surface",
    blurb: "Ledger + policy",
    href: "/org",
    authorizeHref: "/org",
    mark: "An",
    markColor: "#111827",
  },
];

export const BRAND_KIND_LABEL: Record<BrandTile["kind"], string> = {
  agent: "Coding agents",
  pipe: "On the pipe",
  surface: "withOhm surfaces",
};
