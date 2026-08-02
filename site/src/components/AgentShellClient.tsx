"use client";

import { useEffect, useState } from "react";
import { persistKey, readStoredKey } from "@/lib/keyStorage";

const API = "/api/pipe";
const DEMO_PROMPT = "ohm-self-proof-v1";

type Msg = { role: "user" | "assistant" | "system"; content: string };

type DemoResult = {
  first: string;
  second: string;
  events: number | null;
  pipe: number | null;
};

async function chatOnce(
  apiKey: string,
  upstream: string,
  model: string,
  messages: Msg[]
): Promise<{
  cache: string;
  content: string;
  billed: string;
  center: string;
  ok: boolean;
  err?: string;
}> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${apiKey}`,
  };
  if (upstream) headers["X-Ohm-Upstream-Key"] = upstream;
  let res: Response;
  try {
    res = await fetch(`${API}/v1/chat/completions`, {
      method: "POST",
      headers,
      body: JSON.stringify({ model, messages }),
    });
  } catch {
    return {
      cache: "?",
      content: "",
      billed: "",
      center: "",
      ok: false,
      err: "Could not reach the Ohm pipe. Check your connection and try again.",
    };
  }
  const cache = (res.headers.get("x-at-cache") || "?").toUpperCase();
  const billed = res.headers.get("x-at-billed-usd") || "";
  const center = res.headers.get("x-ohm-cost-center") || "";
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    data = { error: { message: "Unexpected response from the pipe." } };
  }
  if (!res.ok) {
    const msg =
      typeof data === "object" &&
      data &&
      "error" in data &&
      typeof (data as { error?: { message?: string } }).error?.message === "string"
        ? (data as { error: { message: string } }).error.message
        : `Request failed (${res.status})`;
    return {
      cache,
      content: "",
      billed,
      center,
      ok: false,
      err: msg,
    };
  }
  const content =
    (data as { choices?: { message?: { content?: string } }[] })?.choices?.[0]
      ?.message?.content || JSON.stringify(data);
  return { cache, content: String(content), billed, center, ok: true };
}

async function ledgerSummary(
  apiKey: string
): Promise<{ events: number | null; pipe: number | null }> {
  try {
    const led = await fetch(`${API}/v1/ledger`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    if (!led.ok) return { events: null, pipe: null };
    const l = await led.json();
    const s = l.summary || {};
    return {
      events: typeof s.event_count === "number" ? s.event_count : null,
      pipe: typeof s.pipe_rent_usd === "number" ? s.pipe_rent_usd : null,
    };
  } catch {
    return { events: null, pipe: null };
  }
}

export function AgentShellClient({
  variant = "workbench",
}: {
  variant?: "demo" | "workbench";
}) {
  const isDemo = variant === "demo";
  const [apiKey, setApiKey] = useState("");
  const [upstream, setUpstream] = useState("");
  const [model, setModel] = useState("mock");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [meta, setMeta] = useState(
    isDemo
      ? "Paste your key, then prove miss → HIT."
      : "Ready — traffic goes only through withOhm."
  );
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const stored = readStoredKey();
    if (stored) setApiKey(stored);
  }, []);

  function onKeyChange(value: string) {
    setApiKey(value);
    if (value.trim().startsWith("sk-at-")) persistKey(value.trim());
  }

  async function send() {
    if (!apiKey || !input.trim()) return;
    const next: Msg[] = [...messages, { role: "user", content: input.trim() }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setDemoResult(null);
    try {
      const r = await chatOnce(apiKey, upstream, model, next);
      if (!r.ok) {
        setMeta(r.err || "Error");
        return;
      }
      setMessages((m) => [...m, { role: "assistant", content: r.content }]);
      const led = await ledgerSummary(apiKey);
      setMeta(
        `Cache ${r.cache}` +
          (r.billed ? ` · billed $${r.billed}` : "") +
          (r.center ? ` · ${r.center}` : "") +
          (led.events != null ? ` · ${led.events} ledger events` : "") +
          (led.pipe != null ? ` · pipe $${led.pipe}` : "")
      );
    } catch (e) {
      setMeta(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runMissHitDemo() {
    if (!apiKey) return;
    setBusy(true);
    setDemoResult(null);
    const demoMessages: Msg[] = [{ role: "user", content: DEMO_PROMPT }];
    setMessages(demoMessages);
    setMeta("Sending identical prompt twice…");
    try {
      const first = await chatOnce(apiKey, upstream, model, demoMessages);
      if (!first.ok) {
        setMeta(first.err || "First call failed");
        return;
      }
      setMessages([
        ...demoMessages,
        { role: "assistant", content: first.content },
      ]);
      const second = await chatOnce(apiKey, upstream, model, demoMessages);
      if (!second.ok) {
        setMeta(second.err || "Second call failed");
        return;
      }
      setMessages([
        ...demoMessages,
        { role: "assistant", content: first.content },
        {
          role: "assistant",
          content: second.content,
        },
      ]);
      const led = await ledgerSummary(apiKey);
      setDemoResult({
        first: first.cache,
        second: second.cache,
        events: led.events,
        pipe: led.pipe,
      });
      const ok =
        first.cache.includes("MISS") && second.cache.includes("HIT");
      setMeta(
        ok
          ? "Hit ratio proof complete — identical traffic replayed from cache."
          : `Finished · first ${first.cache} · second ${second.cache}`
      );
    } catch (e) {
      setMeta(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`agent-shell${isDemo ? " agent-shell--demo" : ""}`}>
      <div className="agent-shell__bar">
        <label>
          withOhm key
          <input
            value={apiKey}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder="sk-at-…"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        {!isDemo ? (
          <label>
            Upstream (BYOK)
            <input
              value={upstream}
              onChange={(e) => setUpstream(e.target.value)}
              placeholder="Optional for mock"
              autoComplete="off"
            />
          </label>
        ) : null}
        <label>
          Model
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            readOnly={isDemo}
          />
        </label>
      </div>

      <p className="agent-shell__meta" aria-live="polite">
        {meta}
      </p>

      {demoResult ? (
        <div className="demo-result" aria-live="polite">
          <div className="demo-result__call">
            <span className="demo-result__label">First call</span>
            <span
              className={`demo-result__badge demo-result__badge--${demoResult.first.toLowerCase()}`}
            >
              {demoResult.first}
            </span>
          </div>
          <div className="demo-result__arrow" aria-hidden="true">
            →
          </div>
          <div className="demo-result__call">
            <span className="demo-result__label">Second call</span>
            <span
              className={`demo-result__badge demo-result__badge--${demoResult.second.toLowerCase()}`}
            >
              {demoResult.second}
            </span>
          </div>
          {(demoResult.events != null || demoResult.pipe != null) && (
            <p className="demo-result__ledger">
              Ledger
              {demoResult.events != null
                ? ` · ${demoResult.events} events`
                : ""}
              {demoResult.pipe != null
                ? ` · pipe rent $${demoResult.pipe}`
                : ""}
            </p>
          )}
        </div>
      ) : null}

      <div className="agent-shell__thread">
        {messages.length === 0 ? (
          <p className="agent-shell__empty">
            {isDemo
              ? "One click sends a fixed prompt twice. Identical bytes replay from Redis on the second call."
              : "Chat stays on the pipe. Identical prompts replay from Redis."}
          </p>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={`agent-shell__msg agent-shell__msg--${m.role}`}
            >
              <strong>{m.role === "user" ? "prompt" : "response"}</strong>
              <pre>{m.content}</pre>
            </div>
          ))
        )}
      </div>

      <div className="agent-shell__compose">
        {!isDemo ? (
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={3}
            placeholder="Message…"
            disabled={busy}
          />
        ) : null}
        <div className="cta-row">
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy || !apiKey.trim()}
            onClick={runMissHitDemo}
          >
            {busy ? "Running…" : "Prove miss → HIT"}
          </button>
          {!isDemo ? (
            <button
              type="button"
              className="btn"
              disabled={busy || !apiKey || !input.trim()}
              onClick={send}
            >
              Send via Ohm
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
