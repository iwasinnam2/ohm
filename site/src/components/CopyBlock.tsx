"use client";

import { useState } from "react";

type CopyBlockProps = {
  /** Text rendered in the block and written to the clipboard. */
  text: string;
  /** Human name for the content, used in the button label and announcement. */
  label: string;
  compact?: boolean;
};

/** A copyable code block: keyboard-focusable, with an announced copy action. */
export function CopyBlock({ text, label, compact }: CopyBlockProps) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Async clipboard denied (embedded webviews, older browsers): fall back
      // to a selection-based copy so the button still works.
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
      } finally {
        document.body.removeChild(ta);
      }
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className={compact ? "copy-block copy-block--compact" : "copy-block"}>
      <pre className="copy-block__pre" tabIndex={0} aria-label={label}>
        {text}
      </pre>
      <button
        type="button"
        className="btn btn--ghost copy-block__btn"
        aria-label={`Copy ${label}`}
        onClick={copy}
      >
        {copied ? "Copied" : "Copy"}
      </button>
      <span role="status" className="visually-hidden">
        {copied ? `${label} copied to clipboard` : ""}
      </span>
    </div>
  );
}
