import Link from "next/link";
import { StartOrProfileCta } from "@/components/StartOrProfileCta";

export default function NotFound() {
  return (
    <>
      <header className="page-head">
        <h1>Page not found</h1>
        <p>
          That address doesn&apos;t exist — but nothing you were doing is lost.
          The pipe is one click away.
        </p>
      </header>
      <div className="cta-row">
        <StartOrProfileCta className="btn btn--primary" />
        <Link href="/" className="link-quiet">
          Home
        </Link>
        <Link href="/docs" className="link-quiet">
          Docs
        </Link>
        <Link href="/support" className="link-quiet">
          Support
        </Link>
      </div>
    </>
  );
}
