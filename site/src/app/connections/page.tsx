import type { Metadata } from "next";
import { ConnectionsClient } from "@/components/ConnectionsClient";

export const metadata: Metadata = {
  title: "Connections",
  description:
    "Interconnectedness and accessibility — connect withOhm to Cursor, Claude Code, VS Code, Windsurf, Zed, and the pipe stack.",
};

export default function ConnectionsPage() {
  return <ConnectionsClient />;
}
