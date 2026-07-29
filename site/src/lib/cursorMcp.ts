/** Cursor MCP one-click install deeplink helpers. */

export type OhmMcpEnv = {
  apiKey: string;
  upstreamKey?: string;
  baseUrl?: string;
};

/** Server config blob (name is a separate query param). */
export function ohmMcpConfig(env: OhmMcpEnv): Record<string, unknown> {
  return {
    command: "python",
    args: ["-m", "ohm_mcp"],
    env: {
      OHM_BASE_URL: env.baseUrl || "http://127.0.0.1:8081/v1",
      OHM_API_KEY: env.apiKey,
      OHM_UPSTREAM_KEY: env.upstreamKey || "",
    },
  };
}

export function encodeMcpConfig(config: Record<string, unknown>): string {
  const json = JSON.stringify(config);
  if (typeof window === "undefined") {
    return Buffer.from(json, "utf8").toString("base64");
  }
  // UTF-8 safe browser base64
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  bytes.forEach((b) => {
    binary += String.fromCharCode(b);
  });
  return btoa(binary);
}

/**
 * Opens Cursor’s built-in MCP install confirm with Ohm pre-filled.
 * @see https://cursor.com/docs/mcp/install-links
 */
export function cursorOhmInstallHref(env: OhmMcpEnv): string {
  const config = encodeMcpConfig(ohmMcpConfig(env));
  const name = encodeURIComponent("ohm");
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=${name}&config=${config}`;
}
