"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = "/api/pipe";
const DEMO_PROMPT = "ohm-self-proof-v1";
const DEMO_PATH = "self-proof";

type CallResult = {
  cache: string;
  billed: string;
  content: string;
  ok: boolean;
  err?: string;
};

type Proof = {
  first: CallResult;
  second: CallResult;
  proofOk: boolean;
};

type ReceiptMint = {
  receipt_url: string;
  badge_markdown: string;
  err?: string;
};

async function chatOnce(apiKey: string): Promise<CallResult> {
  try {
    const res = await fetch(`${API}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
        "X-Ohm-Path": DEMO_PATH,
      },
      body: JSON.stringify({
        model: "mock",
        messages: [{ role: "user", content: DEMO_PROMPT }],
        ohm_path: DEMO_PATH,
      }),
    });
    const cache = (res.headers.get("x-at-cache") || "?").toUpperCase();
    const billed = res.headers.get("x-at-billed-usd") || "";
    let data: unknown;
    try {
      data = await res.json();
    } catch {
      return {
        cache,
        billed,
        content: "",
        ok: false,
        err: "Unexpected response from the pipe.",
      };
    }
    if (!res.ok) {
      const msg =
        typeof data === "object" &&
        data &&
        "error" in data &&
        typeof (data as { error?: { message?: string } }).error?.message ===
          "string"
          ? (data as { error: { message: string } }).error.message
          : `Request failed (${res.status})`;
      return { cache, billed, content: "", ok: false, err: msg };
    }
    const content =
      (data as { choices?: { message?: { content?: string } }[] })?.choices?.[0]
        ?.message?.content || "";
    return { cache, billed, content: String(content), ok: true };
  } catch {
    return {
      cache: "?",
      billed: "",
      content: "",
      ok: false,
      err: "Could not reach the Ohm pipe.",
    };
  }
}

async function mintReceiptOnce(
  apiKey: string,
  displayName: string,
): Promise<ReceiptMint> {
  try {
    const res = await fetch(`${API}/v1/savings/receipt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ display_name: displayName }),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg =
        typeof data?.detail === "string"
          ? data.detail
          : data?.error?.message || `Mint failed (${res.status})`;
      return { receipt_url: "", badge_markdown: "", err: msg };
    }
    const avoided = Number(
      data?.receipt?.estimated_provider_avoided_usd ??
        data?.receipt?.estimated_upstream_avoided_usd ??
        0,
    );
    const hits = Number(data?.receipt?.cache_hit_tokens ?? 0);
    if (!hits && avoided <= 0) {
      return {
        receipt_url: "",
        badge_markdown: "",
        err: "Need accrued cache hits — wait a second and mint again.",
      };
    }
    return {
      receipt_url: String(data.receipt_url || ""),
      badge_markdown: String(data.badge_markdown || ""),
    };
  } catch (e) {
    return { receipt_url: "", badge_markdown: "", err: String(e) };
  }
}

function formatBilled(billed: string): string {
  if (!billed) return "—";
  const n = Number(billed);
  if (!Number.isFinite(n)) return `$${billed}`;
  return `$${n.toFixed(6)}`;
}

export function WasteCheckClient() {
  const [apiKey, setApiKey] = useState("");
  const [usingPublicKey, setUsingPublicKey] = useState(false);
  const [publicKeyReady, setPublicKeyReady] = useState<boolean | null>(null);
  const [manualKey, setManualKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [meta, setMeta] = useState("Loading public proof session…");
  const [proof, setProof] = useState<Proof | null>(null);
  const [receiptName, setReceiptName] = useState("Cursor Pro+ waste check");
  const [receipt, setReceipt] = useState<ReceiptMint | null>(null);
  const [mintBusy, setMintBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/demo-session");
        const data = await res.json();
        if (cancelled) return;
        if (res.ok && data.available && typeof data.apiKey === "string") {
          setApiKey(data.apiKey);
          setUsingPublicKey(true);
          setPublicKeyReady(true);
          setMeta(
            "Public proof key ready — mock model. One click sends the same prompt twice.",
          );
        } else {
          setPublicKeyReady(false);
          setMeta(
            "Public proof key not configured yet. Paste a sk-at-… key, or get a $0 seat.",
          );
        }
      } catch {
        if (!cancelled) {
          setPublicKeyReady(false);
          setMeta("Could not load public proof session. Paste a sk-at-… key.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const effectiveKey = usingPublicKey ? apiKey : manualKey.trim();

  const runProof = useCallback(async () => {
    if (!effectiveKey) return;
    setBusy(true);
    setProof(null);
    setReceipt(null);
    setMeta("Sending identical prompt twice…");
    try {
      const first = await chatOnce(effectiveKey);
      if (!first.ok) {
        setMeta(first.err || "First call failed");
        return;
      }
      const second = await chatOnce(effectiveKey);
      if (!second.ok) {
        setMeta(second.err || "Second call failed");
        return;
      }
      const proofOk =
        first.cache.includes("MISS") && second.cache.includes("HIT");
      setProof({ first, second, proofOk });
      setMeta(
        proofOk
          ? "Proof complete — call 2 replayed from cache. Mint a receipt and share it."
          : `Finished · first ${first.cache} · second ${second.cache}`,
      );
    } catch (e) {
      setMeta(String(e));
    } finally {
      setBusy(false);
    }
  }, [effectiveKey]);

  async function mintPublicReceipt() {
    if (!effectiveKey) return;
    setMintBusy(true);
    setReceipt(null);
    try {
      let result = await mintReceiptOnce(effectiveKey, receiptName);
      if (result.err?.includes("Need accrued cache hits")) {
        await new Promise((r) => setTimeout(r, 800));
        result = await mintReceiptOnce(effectiveKey, receiptName);
      }
      setReceipt(result);
      if (result.err) setMeta(result.err);
      else if (result.receipt_url)
        setMeta("Public receipt minted — share it, then claim the $35 bounty.");
    } finally {
      setMintBusy(false);
    }
  }

  async function copyReceipt() {
    if (!receipt?.receipt_url) return;
    try {
      await navigator.clipboard.writeText(receipt.receipt_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  const tweetHref = receipt?.receipt_url
    ? `https://twitter.com/intent/tweet?text=${encodeURIComponent(
        "I ran the withOhm waste check — identical agent call twice: MISS then HIT. Second call did not re-buy the model.",
      )}&url=${encodeURIComponent(receipt.receipt_url)}`
    : "";

  return (
    <div className="waste-check">
      <div className="waste-check__session" aria-live="polite">
        {usingPublicKey && publicKeyReady ? (
          <p className="waste-check__key-note">
            Using <strong>public proof key</strong> — <code>model: mock</code>{" "}
            only (proves the cache). Real models work the same through the pipe
            once you{" "}
            <Link href="/billing/intermediate">get a $0 seat</Link>.
          </p>
        ) : (
          <label className="billing-form__field">
            <span>withOhm key</span>
            <input
              value={manualKey}
              onChange={(e) => {
                setManualKey(e.target.value);
                setUsingPublicKey(false);
              }}
              placeholder="sk-at-…"
              autoComplete="off"
              spellCheck={false}
            />
          </label>
        )}
        {publicKeyReady === false ? (
          <p className="receipt__foot">
            Need a key?{" "}
            <Link href="/billing/intermediate">Start — $0 seat</Link>
            {" · "}
            <Link href="/keys">API keys</Link>
          </p>
        ) : null}
      </div>

      <p className="agent-shell__meta" aria-live="polite">
        {meta}
      </p>

      <div className="cta-row waste-check__actions">
        <button
          type="button"
          className="btn btn--primary"
          disabled={busy || !effectiveKey}
          onClick={runProof}
        >
          {busy ? "Running…" : "Prove miss → HIT"}
        </button>
        <Link href="/i" className="link-quiet">
          Attach in Cursor
        </Link>
      </div>

      {proof ? (
        <div className="demo-result" aria-live="polite">
          <div className="demo-result__row">
            <div className="demo-result__call">
              <span className="demo-result__label">First call</span>
              <span
                className={`demo-result__badge demo-result__badge--${proof.first.cache.toLowerCase()}`}
              >
                {proof.first.cache}
              </span>
              <span className="demo-result__billed">
                billed {formatBilled(proof.first.billed)}
              </span>
            </div>
            <div className="demo-result__arrow" aria-hidden="true">
              →
            </div>
            <div className="demo-result__call">
              <span className="demo-result__label">Second call</span>
              <span
                className={`demo-result__badge demo-result__badge--${proof.second.cache.toLowerCase()}`}
              >
                {proof.second.cache}
              </span>
              <span className="demo-result__billed">
                billed {formatBilled(proof.second.billed)}
              </span>
            </div>
          </div>
          {proof.proofOk ? (
            <p className="demo-result__punchline">
              Call 2 did not re-buy the model. That&apos;s the waste your agent
              loops are printing — retries, research re-fetches, identical
              prompts — the same pattern that burns a Cursor Pro+ quota mid-month.
            </p>
          ) : (
            <p className="demo-result__punchline">
              Expected MISS then HIT. Got {proof.first.cache} →{" "}
              {proof.second.cache}. Try once more, or{" "}
              <Link href="/contact">tell us</Link>.
            </p>
          )}

          {proof.proofOk ? (
            <div className="demo-result__receipt">
              <label className="billing-form__field">
                <span>Receipt display name</span>
                <input
                  value={receiptName}
                  onChange={(e) => setReceiptName(e.target.value)}
                  autoComplete="off"
                />
              </label>
              <button
                type="button"
                className="btn btn--primary"
                disabled={mintBusy || !effectiveKey}
                onClick={mintPublicReceipt}
              >
                {mintBusy ? "Minting…" : "Mint public receipt"}
              </button>
              {receipt?.err ? (
                <p className="demo-result__ledger">{receipt.err}</p>
              ) : null}
              {receipt?.receipt_url ? (
                <div className="demo-result__share">
                  <p>
                    <a
                      href={receipt.receipt_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {receipt.receipt_url}
                    </a>
                  </p>
                  <div className="cta-row">
                    <button
                      type="button"
                      className="btn"
                      onClick={copyReceipt}
                    >
                      {copied ? "Copied" : "Copy link"}
                    </button>
                    {tweetHref ? (
                      <a
                        className="btn"
                        href={tweetHref}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Share on X
                      </a>
                    ) : null}
                    <Link href="/bounty" className="btn btn--primary">
                      Claim $35 bounty
                    </Link>
                  </div>
                  {receipt.badge_markdown ? (
                    <pre className="org-console__log">
                      {receipt.badge_markdown}
                    </pre>
                  ) : null}
                  {!usingPublicKey ? null : (
                    <p className="receipt__foot">
                      Bounty credit needs your own seat key —{" "}
                      <Link href="/billing/intermediate">$0 Intermediate</Link>
                      , re-run the check, mint under your name, then email{" "}
                      <a href="mailto:partners@withohm.dev">
                        partners@withohm.dev
                      </a>
                      .
                    </p>
                  )}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
