import type { Metadata } from "next";
import { InstallClient } from "@/components/InstallClient";

export const metadata: Metadata = {
  title: "Install",
  description:
    "Add withOhm MCP from https://withohm.dev/i — compliant fetch for agents.",
};

export default function InstallPage() {
  return <InstallClient />;
}
