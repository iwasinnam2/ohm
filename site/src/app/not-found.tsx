import Link from "next/link";

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
        <Link href="/billing/intermediate" className="btn btn--primary">
          Start now — $0 seat
        </Link>
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
