import type { Metadata } from "next";
import { KeysConsole } from "@/components/KeysConsole";

export const metadata: Metadata = {
  title: "API keys",
  description:
    "Create, reveal, restore, and delete withOhm secret API keys after you subscribe. Secrets are shown once at issue.",
};

export default function KeysPage() {
  return <KeysConsole />;
}
