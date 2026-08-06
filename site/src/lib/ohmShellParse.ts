/** Minimal PowerShell-ish tokenizer for the Agent Shell. */

export type ShellArg = { name?: string; value: string };

export type ParsedLine = {
  command: string;
  args: ShellArg[];
  /** Remaining positional values in order */
  positionals: string[];
  named: Record<string, string>;
};

/** Split a line into tokens, respecting double quotes. */
export function tokenize(line: string): string[] {
  const tokens: string[] = [];
  let cur = "";
  let inQuote = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]!;
    if (ch === '"') {
      inQuote = !inQuote;
      continue;
    }
    if (!inQuote && /\s/.test(ch)) {
      if (cur) {
        tokens.push(cur);
        cur = "";
      }
      continue;
    }
    cur += ch;
  }
  if (cur) tokens.push(cur);
  return tokens;
}

export function parseLine(raw: string): ParsedLine | null {
  const trimmed = raw.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;

  const tokens = tokenize(trimmed);
  if (tokens.length === 0) return null;

  const command = tokens[0]!;
  const args: ShellArg[] = [];
  const positionals: string[] = [];
  const named: Record<string, string> = {};

  let i = 1;
  while (i < tokens.length) {
    const t = tokens[i]!;
    if (t.startsWith("-") && t.length > 1) {
      const body = t.slice(1);
      if (body.includes(":")) {
        const [n, ...rest] = body.split(":");
        const value = rest.join(":");
        args.push({ name: n!, value });
        named[n!.toLowerCase()] = value;
        i += 1;
        continue;
      }
      const next = tokens[i + 1];
      if (next !== undefined && !next.startsWith("-")) {
        args.push({ name: body, value: next });
        named[body.toLowerCase()] = next;
        i += 2;
        continue;
      }
      // switch
      args.push({ name: body, value: "true" });
      named[body.toLowerCase()] = "true";
      i += 1;
      continue;
    }
    args.push({ value: t });
    positionals.push(t);
    i += 1;
  }

  return { command, args, positionals, named };
}

export function namedOr(
  named: Record<string, string>,
  keys: string[],
  fallback = "",
): string {
  for (const k of keys) {
    const v = named[k.toLowerCase()];
    if (v !== undefined && v !== "") return v;
  }
  return fallback;
}
