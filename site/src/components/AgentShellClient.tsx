"use client";

import { useState } from "react";

const API = (
  process.env.NEXT_PUBLIC_OHM_API_URL || "https://api.withohm.dev"
).replace(/\/$/, "");

type Msg = { role: "user" | "assistant" | "system"; content: string };

export function AgentShellClient() {
  const [apiKey, setApiKey] = useState("");
  const [upstream, setUpstream] = useState("");
  const [model, setModel] = useState("mock");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [meta, setMeta] = useState("Ready — traffic goes only through withOhm.");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!apiKey || !input.trim()) return;
    const next: Msg[] = [...messages, { role: "user", content: input.trim() }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      };
      if (upstream) headers["X-Ohm-Upstream-Key"] = upstream;
      const res = await fetch(`${API}/v1/chat/completions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ model, messages: next }),
      });
      const cache = res.headers.get("x-at-cache") || "?";
      const billed = res.headers.get("x-at-billed-usd") || "";
      const center = res.headers.get("x-ohm-cost-center") || "";
      const data = await res.json();
      if (!res.ok) {
        setMeta(`Error ${res.status}: ${JSON.stringify(data)}`);
        return;
      }
      const content =
        data?.choices?.[0]?.message?.content || JSON.stringify(data);
      setMessages((m) => [...m, { role: "assistant", content: String(content) }]);
      setMeta(
        `X-AT-Cache: ${cache}` +
          (billed ? ` · billed $${billed}` : "") +
          (center ? ` · cost_center ${center}` : "")
      );
      // Refresh tenant ledger strip
      const led = await fetch(`${API}/v1/ledger`, {
        headers: { Authorization: `Bearer ${apiKey}` },
      });
      if (led.ok) {
        const l = await led.json();
        const s = l.summary || {};
        setMeta(
          (m) =>
            `${m} · ledger events ${s.event_count ?? 0} · pipe $${s.pipe_rent_usd ?? 0}`
        );
      }
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
      <div className="agent-shell__thread">
        {messages.length === 0 ? (
          <p className="agent-shell__empty">
            Chat stays on the pipe. Identical prompts replay from Redis.
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
        <button
          type="button"
          className="btn btn--primary"
          disabled={busy || !apiKey || !input.trim()}
          onClick={send}
        >
          Send via Ohm
        </button>
      </div>
    </div>
  );
}
