import type { Metadata } from "next";
import { ConnectionsClient } from "@/components/ConnectionsClient";

export const metadata: Metadata = {
  title: "Connections",
  description:
    "Connect withOhm to Cursor, Claude Code, VS Code, Windsurf, and Zed — one MCP attach, seven tools, keys that stay yours.",
};

export default function ConnectionsPage() {
  return <ConnectionsClient />;
}
