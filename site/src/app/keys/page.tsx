import type { Metadata } from "next";
import { KeysConsole } from "@/components/KeysConsole";

export const metadata: Metadata = {
  title: "API keys",
  description:
    "Find, reveal, and restore your withOhm secret API keys. Secrets are shown once at issue — this page recovers what this browser still holds.",
};

export default function KeysPage() {
  return <KeysConsole />;
}
