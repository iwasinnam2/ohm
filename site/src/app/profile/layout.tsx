import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Profile",
  description:
    "Your withOhm Intermediate seat — organisation, email, and API key shortcuts.",
  robots: { index: false, follow: false },
};

export default function ProfileLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
