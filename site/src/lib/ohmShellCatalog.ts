/** MCP skills + product features advertised in the Agent Shell banner. */

export type OhmShellSkill = {
  name: string;
  cmdlet: string;
  summary: string;
};

export type OhmShellFeature = {
  name: string;
  summary: string;
};

/** Skills shipped with withohm-mcp / .cursor/skills */
export const OHM_MCP_SKILLS: OhmShellSkill[] = [
  {
    name: "ohm_chat",
    cmdlet: "Invoke-OhmChat",
    summary: "OpenAI-compatible chat through the pipe; Redis exact-replay on identical prompts",
  },
  {
    name: "ohm_fetch_web",
    cmdlet: "Invoke-OhmFetch",
    summary: "Compliant public URL → markdown/JSON (robots-gated, purpose-bound)",
  },
  {
    name: "ohm_usage",
    cmdlet: "Get-OhmUsage",
    summary: "Hit ratio, fetch meters, estimated pipe rent",
  },
  {
    name: "ohm_models",
    cmdlet: "Get-OhmModel",
    summary: "Model ids the pipe routes (including BYOK upstreams)",
  },
  {
    name: "ohm_savings",
    cmdlet: "Get-OhmSaving",
    summary: "Dual ledger — estimated provider $ avoided vs pipe rent",
  },
  {
    name: "ohm_receipt",
    cmdlet: "New-OhmReceipt",
    summary: "Mint a public /r/… savings receipt + README badge",
  },
  {
    name: "ohm_providers",
    cmdlet: "Get-OhmProvider",
    summary: "Upstream / failover readiness for the pipe",
  },
  {
    name: "ohm_policy",
    cmdlet: "Get-OhmPolicy",
    summary: "Compliance policy — allowed fetch purposes and limits",
  },
];

export const OHM_FEATURES: OhmShellFeature[] = [
  {
    name: "OpenAI-compatible pipe",
    summary: "One base URL · BYOK · api.withohm.dev/v1",
  },
  {
    name: "Cache trees",
    summary: "Tip / fork / promote / freeze exact-replay inventory (X-Ohm-Cache-Tree)",
  },
  {
    name: "Middleware governance",
    summary: "Compose with Neon AI Gateway beta on the same PR slug",
  },
  {
    name: "Streaming failover",
    summary: "Pre-first-byte retry — honest non-200 on failure",
  },
  {
    name: "Signed receipts",
    summary: "X-Ohm-Receipt + JWKS — verify HITs yourself",
  },
  {
    name: "Org / FinOps",
    summary: "Cost centers, ledger export, spend caps, SSO path",
  },
];

export function buildBanner(): string {
  const skillLines = OHM_MCP_SKILLS.map(
    (s) => `  ${s.name.padEnd(16)} ${s.cmdlet.padEnd(18)} ${s.summary}`,
  ).join("\n");
  const featureLines = OHM_FEATURES.map(
    (f) => `  ${f.name.padEnd(24)} ${f.summary}`,
  ).join("\n");

  return [
    "withOhm Agent Shell  ·  PowerShell-compatible CLI on the pipe",
    "Copyright (c) withOhm. Middleware governance — rent the plumbing.",
    "",
    "MCP skills (pip install withohm-mcp  →  ohm-mcp)",
    skillLines,
    "",
    "Product features",
    featureLines,
    "",
    "Type Get-Help or Get-Command for cmdlets. Set-OhmKey -Key sk-at-… to authenticate.",
  ].join("\n");
}
