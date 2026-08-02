"use client";

import { useState } from "react";

// Always same-origin — browser→api.withohm.dev lacks CORS until the edge roll.
const API = "/api/pipe";

const DEMO_PROMPT = "ohm-self-proof-v1";

type Msg = { role: "user" | "assistant" | "system"; content: string };

async function chatOnce(
  apiKey: string,
  upstream: string,
  model: string,
  messages: Msg[]
): Promise<{ cache: string; content: string; billed: string; center: string; ok: boolean; err?: string }> {
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
  } catch (e) {
    return {
      cache: "?",
      content: "",
      billed: "",
      center: "",
      ok: false,
      err:
        `Network error talking to ${API}: ${String(e)}. ` +
        "If this is a CORS/edge issue, the site should use /api/pipe — hard-refresh and retry.",
    };
  }
  const cache = res.headers.get("x-at-cache") || "?";
  const billed = res.headers.get("x-at-billed-usd") || "";
  const center = res.headers.get("x-ohm-cost-center") || "";
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    data = { error: { message: await res.text().catch(() => "non-JSON body") } };
  }
  if (!res.ok) {
    return {
      cache,
      content: "",
      billed,
      center,
      ok: false,
      err: `Error ${res.status}: ${JSON.stringify(data)}`,
    };
  }
  const content =
    (data as { choices?: { message?: { content?: string } }[] })?.choices?.[0]
      ?.message?.content || JSON.stringify(data);
  return { cache, content: String(content), billed, center, ok: true };
}

async function ledgerStrip(apiKey: string): Promise<string> {
  const led = await fetch(`${API}/v1/ledger`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  if (!led.ok) return "";
  const l = await led.json();
  const s = l.summary || {};
  return ` · ledger events ${s.event_count ?? 0} · pipe $${s.pipe_rent_usd ?? 0}`;
}

export function AgentShellClient() {
  const [apiKey, setApiKey] = useState("");
  const [upstream, setUpstream] = useState("");
  const [model, setModel] = useState("mock");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [meta, setMeta] = useState("Ready — traffic goes only through withOhm.");
  const [demoStrip, setDemoStrip] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!apiKey || !input.trim()) return;
    const next: Msg[] = [...messages, { role: "user", content: input.trim() }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setDemoStrip("");
    try {
      const r = await chatOnce(apiKey, upstream, model, next);
      if (!r.ok) {
        setMeta(r.err || "Error");
        return;
      }
      setMessages((m) => [...m, { role: "assistant", content: r.content }]);
      let line =
        `X-AT-Cache: ${r.cache}` +
        (r.billed ? ` · billed $${r.billed}` : "") +
        (r.center ? ` · cost_center ${r.center}` : "");
      line += await ledgerStrip(apiKey);
      setMeta(line);
    } catch (e) {
      setMeta(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runMissHitDemo() {
    if (!apiKey) return;
    setBusy(true);
    setDemoStrip("");
    const demoMessages: Msg[] = [{ role: "user", content: DEMO_PROMPT }];
    setMessages(demoMessages);
    setMeta("Demo: sending identical prompt twice…");
    try {
      const first = await chatOnce(apiKey, upstream, model, demoMessages);
      if (!first.ok) {
        setMeta(first.err || "Demo failed on first call");
        return;
      }
      setMessages([
        ...demoMessages,
        { role: "assistant", content: first.content },
      ]);
      const second = await chatOnce(apiKey, upstream, model, demoMessages);
      if (!second.ok) {
        setMeta(second.err || "Demo failed on second call");
        return;
      }
      setMessages([
        ...demoMessages,
        { role: "assistant", content: first.content },
        {
          role: "assistant",
          content: `(replay)\n${second.content}`,
        },
      ]);
      const strip = await ledgerStrip(apiKey);
      setDemoStrip(
        `MISS→HIT: first=${first.cache} · second=${second.cache}`
      );
      setMeta(
        `Demo done · 1st X-AT-Cache: ${first.cache} · 2nd X-AT-Cache: ${second.cache}${strip}`
      );
    } catch (e) {
      setMeta(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="agent-shell">
      <div className="agent-shell__bar">
        <label>
          Ohm key
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-at-…"
            autoComplete="off"
          />
        </label>
        <label>
          Upstream (BYOK)
          <input
            value={upstream}
            onChange={(e) => setUpstream(e.target.value)}
            placeholder="sk-… (optional for mock)"
            autoComplete="off"
          />
        </label>
        <label>
          Model
          <input value={model} onChange={(e) => setModel(e.target.value)} />
        </label>
      </div>
      <p className="agent-shell__meta" aria-live="polite">
        {meta}
      </p>
      {demoStrip ? (
        <p className="agent-shell__demo" aria-live="polite">
          {demoStrip}
        </p>
      ) : null}
      <div className="agent-shell__thread">
        {messages.length === 0 ? (
          <p className="agent-shell__empty">
            Chat stays on the pipe. Identical prompts replay from Redis.
            Use <strong>Run miss→HIT demo</strong> for a one-click proof
            (model <code>mock</code>, no BYOK).
          </p>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`agent-shell__msg agent-shell__msg--${m.role}`}>
              <strong>{m.role}</strong>
              <pre>{m.content}</pre>
            </div>
          ))
        )}
      </div>
      <div className="agent-shell__compose">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          placeholder="Message…"
          disabled={busy}
        />
        <div className="cta-row">
          <button
            type="button"
            className="btn btn--primary"
            disabled={busy || !apiKey || !input.trim()}
            onClick={send}
          >
            Send via Ohm
          </button>
          <button
            type="button"
            className="btn"
            disabled={busy || !apiKey}
            onClick={runMissHitDemo}
          >
            Run miss→HIT demo
          </button>
        </div>
      </div>
    </div>
  );
}
