import type { Metadata } from "next";
import { InstallClient } from "@/components/InstallClient";

export const metadata: Metadata = {
  title: "Install",
  description:
    "Install withOhm — Agent Shell or OpenAI-compatible base URL. MCP/Cursor optional.",
};

export default function InstallPage() {
  return <InstallClient />;
}
