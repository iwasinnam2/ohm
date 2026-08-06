"use client";

import { useEffect, useRef, useState } from "react";
import { persistKey, readStoredKey } from "@/lib/keyStorage";
import { buildBanner, OHM_MCP_SKILLS } from "@/lib/ohmShellCatalog";
import { namedOr, parseLine } from "@/lib/ohmShellParse";

const API = "/api/pipe";

type LineKind = "out" | "err" | "cmd" | "sys";
type TermLine = { kind: LineKind; text: string };

type Session = {
  apiKey: string;
  upstream: string;
  model: string;
  path: string;
};

function promptFor(session: Session): string {
  const auth = session.apiKey.trim() ? "ohm" : "guest";
  return `PS withOhm:\\${auth}>`;
}

async function pipeGet(
  path: string,
  apiKey: string,
): Promise<{ ok: boolean; text: string; status: number }> {
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    const text = await res.text();
    return { ok: res.ok, text, status: res.status };
  } catch {
    return { ok: false, text: "Could not reach the Ohm pipe.", status: 0 };
  }
}

async function pipeChat(
  session: Session,
  prompt: string,
  fetchUrls?: string[],
): Promise<{ ok: boolean; text: string; cache: string }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.apiKey}`,
  };
  if (session.upstream) headers["X-Ohm-Upstream-Key"] = session.upstream;
  const p = session.path.trim().toLowerCase();
  if (p) headers["X-Ohm-Path"] = p;

  const body: Record<string, unknown> = {
    model: session.model,
    messages: [{ role: "user", content: prompt }],
    ...(p ? { ohm_path: p } : {}),
  };
  if (fetchUrls?.length) {
    body.fetch_web_context = true;
    body.web_purpose = "public_web_retrieval";
    body.web_urls = fetchUrls;
  }

  try {
    const res = await fetch(`${API}/v1/chat/completions`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const cache = (res.headers.get("x-at-cache") || "?").toUpperCase();
    let data: unknown;
    try {
      data = await res.json();
    } catch {
      return { ok: false, text: "Unexpected response from the pipe.", cache };
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
      return { ok: false, text: msg, cache };
    }
    const content =
      (data as { choices?: { message?: { content?: string } }[] })?.choices?.[0]
        ?.message?.content || JSON.stringify(data);
    return { ok: true, text: String(content), cache };
  } catch {
    return {
      ok: false,
      text: "Could not reach the Ohm pipe.",
      cache: "?",
    };
  }
}

function helpText(): string {
  return [
    "NAME",
    "  withOhm Agent Shell — PowerShell-compatible CLI",
    "",
    "SESSION",
    "  Set-OhmKey -Key sk-at-…",
    "  Set-OhmUpstream -Key <provider-key>     # BYOK on miss",
    "  Set-OhmModel -Name mock|gpt-4o-mini|…",
    "  Set-OhmPath -Path docs-bot",
    "  Get-OhmSession",
    "",
    "MCP SKILLS (cmdlets)",
    ...OHM_MCP_SKILLS.map(
      (s) => `  ${s.cmdlet.padEnd(20)} alias ${s.name}`,
    ),
    "",
    "EXAMPLES",
    '  Invoke-OhmChat -Prompt "ping"',
    '  ohm_chat "hello from the shell"',
    "  Get-OhmUsage",
    '  Invoke-OhmFetch -Uri https://example.com',
    '  New-OhmReceipt -Name "my team"',
    "",
    "  Get-Command          list cmdlets",
    "  Get-OhmSkill         MCP skill catalog",
    "  Get-OhmFeature       product features",
    "  Clear-Host | cls",
    "  Get-Help",
  ].join("\n");
}

function commandList(): string {
  const cmds = [
    "Get-Help",
    "Get-Command",
    "Get-OhmSkill",
    "Get-OhmFeature",
    "Get-OhmSession",
    "Set-OhmKey",
    "Set-OhmUpstream",
    "Set-OhmModel",
    "Set-OhmPath",
    "Invoke-OhmChat (ohm_chat)",
    "Invoke-OhmFetch (ohm_fetch_web)",
    "Get-OhmUsage (ohm_usage)",
    "Get-OhmModel (ohm_models)",
    "Get-OhmSaving (ohm_savings)",
    "New-OhmReceipt (ohm_receipt)",
    "Get-OhmProvider (ohm_providers)",
    "Get-OhmPolicy (ohm_policy)",
    "Clear-Host (cls)",
  ];
  return [
    "CommandType     Name",
    "-----------     ----",
    ...cmds.map((c) => `Cmdlet          ${c}`),
  ].join("\n");
}

export function AgentShellClient({
  variant = "workbench",
}: {
  variant?: "demo" | "workbench";
}) {
  const [session, setSession] = useState<Session>({
    apiKey: "",
    upstream: "",
    model: "mock",
    path: variant === "demo" ? "self-proof" : "",
  });
  const [lines, setLines] = useState<TermLine[]>(() => [
    { kind: "sys", text: buildBanner() },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState(-1);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const stored = readStoredKey();
    if (stored) {
      setSession((s) => ({ ...s, apiKey: stored }));
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [lines, busy]);

  function append(...more: TermLine[]) {
    setLines((prev) => [...prev, ...more]);
  }

  function requireKey(): string | null {
    const k = session.apiKey.trim();
    if (!k) {
      append({
        kind: "err",
        text: "Set-OhmKey -Key sk-at-…  (or paste a key from /keys)",
      });
      return null;
    }
    return k;
  }

  async function runCommand(raw: string) {
    const parsed = parseLine(raw);
    if (!parsed) return;

    const cmd = parsed.command;
    const alias = cmd.toLowerCase();
    const { named, positionals } = parsed;

    // Normalize aliases → canonical
    const canon =
      (
        {
          help: "Get-Help",
          man: "Get-Help",
          "get-help": "Get-Help",
          "get-command": "Get-Command",
          gcm: "Get-Command",
          "get-ohmskill": "Get-OhmSkill",
          "get-ohmfeature": "Get-OhmFeature",
          "get-ohmsession": "Get-OhmSession",
          "set-ohmkey": "Set-OhmKey",
          "set-ohmupstream": "Set-OhmUpstream",
          "set-ohmmodel": "Set-OhmModel",
          "set-ohmpath": "Set-OhmPath",
          "invoke-ohmchat": "Invoke-OhmChat",
          ohm_chat: "Invoke-OhmChat",
          chat: "Invoke-OhmChat",
          "invoke-ohmfetch": "Invoke-OhmFetch",
          ohm_fetch_web: "Invoke-OhmFetch",
          fetch: "Invoke-OhmFetch",
          "get-ohmusage": "Get-OhmUsage",
          ohm_usage: "Get-OhmUsage",
          usage: "Get-OhmUsage",
          "get-ohmmodel": "Get-OhmModel",
          ohm_models: "Get-OhmModel",
          models: "Get-OhmModel",
          "get-ohmsaving": "Get-OhmSaving",
          ohm_savings: "Get-OhmSaving",
          savings: "Get-OhmSaving",
          "new-ohmreceipt": "New-OhmReceipt",
          ohm_receipt: "New-OhmReceipt",
          "get-ohmprovider": "Get-OhmProvider",
          ohm_providers: "Get-OhmProvider",
          "get-ohmpolicy": "Get-OhmPolicy",
          ohm_policy: "Get-OhmPolicy",
          "clear-host": "Clear-Host",
          cls: "Clear-Host",
          clear: "Clear-Host",
        } as Record<string, string>
      )[alias] || cmd;

    switch (canon) {
      case "Get-Help":
        append({ kind: "out", text: helpText() });
        return;
      case "Get-Command":
        append({ kind: "out", text: commandList() });
        return;
      case "Get-OhmSkill":
        append({ kind: "out", text: buildBanner().split("Product features")[0]!.trimEnd() });
        return;
      case "Get-OhmFeature": {
        const feat = buildBanner().split("Product features")[1] ?? "";
        append({
          kind: "out",
          text: `Product features\n${feat.trim()}`,
        });
        return;
      }
      case "Get-OhmSession":
        append({
          kind: "out",
          text: [
            `ApiKey    : ${session.apiKey ? `${session.apiKey.slice(0, 10)}…` : "(not set)"}`,
            `Upstream  : ${session.upstream ? "(set)" : "(none — mock ok)"}`,
            `Model     : ${session.model}`,
            `Path      : ${session.path || "(none)"}`,
            `Pipe      : ${API}/v1`,
          ].join("\n"),
        });
        return;
      case "Set-OhmKey": {
        const key = namedOr(named, ["key", "value", "k"], positionals[0] || "");
        if (!key.startsWith("sk-at-")) {
          append({
            kind: "err",
            text: "Expected a withOhm key starting with sk-at-",
          });
          return;
        }
        setSession((s) => ({ ...s, apiKey: key }));
        persistKey(key);
        append({ kind: "out", text: "Ohm key set for this browser session." });
        return;
      }
      case "Set-OhmUpstream": {
        const key = namedOr(named, ["key", "value", "k"], positionals[0] || "");
        setSession((s) => ({ ...s, upstream: key }));
        append({
          kind: "out",
          text: key
            ? "Upstream BYOK key set (sent as X-Ohm-Upstream-Key on miss)."
            : "Upstream key cleared.",
        });
        return;
      }
      case "Set-OhmModel": {
        const name = namedOr(named, ["name", "model", "m"], positionals[0] || "");
        if (!name) {
          append({ kind: "err", text: "Set-OhmModel -Name <model>" });
          return;
        }
        setSession((s) => ({ ...s, model: name }));
        append({ kind: "out", text: `Model = ${name}` });
        return;
      }
      case "Set-OhmPath": {
        const path = namedOr(named, ["path", "p", "name"], positionals[0] || "");
        setSession((s) => ({ ...s, path }));
        append({
          kind: "out",
          text: path ? `X-Ohm-Path = ${path}` : "Path cleared.",
        });
        return;
      }
      case "Clear-Host":
        setLines([{ kind: "sys", text: buildBanner() }]);
        return;
      case "Invoke-OhmChat": {
        const key = requireKey();
        if (!key) return;
        const prompt = namedOr(
          named,
          ["prompt", "message", "m", "p"],
          positionals.join(" "),
        );
        if (!prompt) {
          append({
            kind: "err",
            text: 'Invoke-OhmChat -Prompt "your message"',
          });
          return;
        }
        setBusy(true);
        try {
          const r = await pipeChat({ ...session, apiKey: key }, prompt);
          if (!r.ok) {
            append({ kind: "err", text: r.text });
          } else {
            append({
              kind: "out",
              text: `[${r.cache}] ${r.text}`,
            });
          }
        } finally {
          setBusy(false);
        }
        return;
      }
      case "Invoke-OhmFetch": {
        const key = requireKey();
        if (!key) return;
        const uri = namedOr(
          named,
          ["uri", "url", "u"],
          positionals[0] || "",
        );
        if (!uri) {
          append({
            kind: "err",
            text: "Invoke-OhmFetch -Uri https://example.com",
          });
          return;
        }
        const query = namedOr(named, ["query", "q"], positionals.slice(1).join(" "));
        setBusy(true);
        try {
          const r = await pipeChat(
            { ...session, apiKey: key },
            query || "Summarize the web context.",
            [uri],
          );
          if (!r.ok) {
            append({ kind: "err", text: r.text });
          } else {
            append({ kind: "out", text: `[fetch ${r.cache}] ${r.text}` });
          }
        } finally {
          setBusy(false);
        }
        return;
      }
      case "Get-OhmUsage":
      case "Get-OhmModel":
      case "Get-OhmSaving":
      case "Get-OhmProvider":
      case "Get-OhmPolicy": {
        const key = requireKey();
        if (!key) return;
        const pathMap: Record<string, string> = {
          "Get-OhmUsage": "/v1/usage",
          "Get-OhmModel": "/v1/models",
          "Get-OhmSaving": "/v1/savings",
          "Get-OhmProvider": "/v1/providers",
          "Get-OhmPolicy": "/v1/compliance/policy",
        };
        setBusy(true);
        try {
          const r = await pipeGet(pathMap[canon]!, key);
          try {
            const pretty = JSON.stringify(JSON.parse(r.text), null, 2);
            append({
              kind: r.ok ? "out" : "err",
              text: r.ok ? pretty : `${r.status}: ${r.text}`,
            });
          } catch {
            append({
              kind: r.ok ? "out" : "err",
              text: r.text,
            });
          }
        } finally {
          setBusy(false);
        }
        return;
      }
      case "New-OhmReceipt": {
        const key = requireKey();
        if (!key) return;
        const name = namedOr(
          named,
          ["name", "displayname", "n"],
          positionals[0] || "withOhm Agent Shell",
        );
        setBusy(true);
        try {
          const res = await fetch(`${API}/v1/savings/receipt`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${key}`,
            },
            body: JSON.stringify({ display_name: name }),
          });
          const text = await res.text();
          try {
            const data = JSON.parse(text);
            if (!res.ok) {
              append({
                kind: "err",
                text:
                  data?.detail ||
                  data?.error?.message ||
                  `Mint failed (${res.status})`,
              });
            } else {
              append({
                kind: "out",
                text: [
                  `ReceiptUrl     : ${data.receipt_url || ""}`,
                  `BadgeMarkdown  :`,
                  data.badge_markdown || "",
                ].join("\n"),
              });
            }
          } catch {
            append({ kind: res.ok ? "out" : "err", text });
          }
        } finally {
          setBusy(false);
        }
        return;
      }
      default:
        append({
          kind: "err",
          text: `${cmd} : The term '${cmd}' is not recognized as a cmdlet. Type Get-Command.`,
        });
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const raw = input.trim();
    if (!raw || busy) return;
    append({ kind: "cmd", text: `${promptFor(session)} ${raw}` });
    setHistory((h) => [...h, raw]);
    setHistIdx(-1);
    setInput("");
    await runCommand(raw);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length === 0) return;
      const next =
        histIdx < 0 ? history.length - 1 : Math.max(0, histIdx - 1);
      setHistIdx(next);
      setInput(history[next] || "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (histIdx < 0) return;
      const next = histIdx + 1;
      if (next >= history.length) {
        setHistIdx(-1);
        setInput("");
      } else {
        setHistIdx(next);
        setInput(history[next] || "");
      }
    } else if (e.key === "l" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      setLines([{ kind: "sys", text: buildBanner() }]);
    }
  }

  return (
    <div
      className="ps-shell"
      onClick={() => inputRef.current?.focus()}
      role="application"
      aria-label="withOhm Agent Shell — PowerShell CLI"
    >
      <div className="ps-shell__titlebar">
        <span className="ps-shell__dots" aria-hidden="true">
          <i /><i /><i />
        </span>
        <span className="ps-shell__title">
          Agent Shell — withOhm {variant === "demo" ? "(demo)" : ""} · Windows
          PowerShell
        </span>
      </div>

      <div className="ps-shell__statusbar" aria-label="Session">
        <span>
          Model <strong>{session.model}</strong>
        </span>
        <span>
          Path <strong>{session.path || "—"}</strong>
        </span>
        <span>
          Key{" "}
          <strong>
            {session.apiKey ? `${session.apiKey.slice(0, 10)}…` : "not set"}
          </strong>
        </span>
        <span className="ps-shell__statusbar-hint">
          Ctrl+L clear · ↑ history · Get-Help
        </span>
      </div>

      <div className="ps-shell__scroll" tabIndex={-1}>
        {lines.map((line, i) => (
          <pre
            key={i}
            className={`ps-shell__line ps-shell__line--${line.kind}`}
          >
            {line.text}
          </pre>
        ))}
        {busy ? (
          <pre className="ps-shell__line ps-shell__line--sys">…</pre>
        ) : null}
        <div ref={bottomRef} />
      </div>

      <form className="ps-shell__prompt" onSubmit={onSubmit}>
        <label className="visually-hidden" htmlFor="ps-shell-input">
          PowerShell command
        </label>
        <span className="ps-shell__prompt-label" aria-hidden="true">
          {promptFor(session)}
        </span>
        <input
          id="ps-shell-input"
          ref={inputRef}
          className="ps-shell__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy}
          autoComplete="off"
          autoCapitalize="off"
          spellCheck={false}
          placeholder='Get-Help   |   Invoke-OhmChat -Prompt "hi"'
        />
      </form>
    </div>
  );
}
