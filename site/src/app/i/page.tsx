import type { Metadata } from "next";
import { InstallClient } from "@/components/InstallClient";

export const metadata: Metadata = {
  title: "Install",
  description:
    "Install withOhm — Agent Shell, OpenAI-compatible base URL, or MCP for Cursor and friends.",
};

export default function InstallPage() {
  return <InstallClient />;
}
