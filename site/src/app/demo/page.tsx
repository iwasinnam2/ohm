import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Waste demo",
  description: "Moved under Product — identical call MISS then HIT.",
};

/** Legacy /demo → Product waste demo. */
export default function DemoRedirectPage() {
  redirect("/product/waste-demo");
}
