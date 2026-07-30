#!/usr/bin/env python3
"""ohm env-pull — Neon-style credential helper for local .env.

Writes OHM_API_KEY / OHM_BASE_URL (and optional OHM_UPSTREAM_KEY) into a dotenv
file. Does not invent keys — pass --api-key or read from the environment /
existing .env.

Examples:
  python scripts/ohm_env_pull.py --api-key sk-at-... --base-url http://localhost:8081/v1
  OHM_API_KEY=sk-at-... python scripts/ohm_env_pull.py --file .env
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _upsert(path: Path, updates: dict[str, str]) -> None:
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    out: list[str] = []
    for line in existing_lines:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", line)
        if m and m.group(1) in updates:
            key = m.group(1)
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, val in updates.items():
        if key not in seen:
            out.append(f"{key}={val}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull Ohm gateway env vars into a .env file")
    ap.add_argument("--file", default=".env", help="Target dotenv path (default .env)")
    ap.add_argument("--api-key", default="", help="Ohm API key (else OHM_API_KEY / AT_API_KEYS)")
    ap.add_argument(
        "--base-url",
        default="",
        help="Gateway base URL (else OHM_BASE_URL; default http://localhost:8081/v1)",
    )
    ap.add_argument("--upstream-key", default="", help="Optional BYOK provider key")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_absolute():
        path = ROOT / path
    existing = _load_dotenv(path)

    api_key = (
        args.api_key.strip()
        or os.environ.get("OHM_API_KEY", "").strip()
        or existing.get("OHM_API_KEY", "").strip()
        or existing.get("AT_API_KEYS", "").split(",")[0].strip()
        or os.environ.get("AT_API_KEYS", "").split(",")[0].strip()
    )
    if not api_key:
        raise SystemExit(
            "No API key: pass --api-key or set OHM_API_KEY (issue via "
            "POST /v1/admin/tenants or Checkout)."
        )

    base = (
        args.base_url.strip()
        or os.environ.get("OHM_BASE_URL", "").strip()
        or existing.get("OHM_BASE_URL", "").strip()
        or "http://localhost:8081/v1"
    )
    upstream = (
        args.upstream_key.strip()
        or os.environ.get("OHM_UPSTREAM_KEY", "").strip()
        or existing.get("OHM_UPSTREAM_KEY", "").strip()
    )

    updates = {
        "OHM_API_KEY": api_key,
        "OHM_BASE_URL": base.rstrip("/"),
    }
    if upstream:
        updates["OHM_UPSTREAM_KEY"] = upstream

    _upsert(path, updates)
    print(f"Wrote {', '.join(updates)} → {path}")
    print("Tip: point OpenAI SDK base_url at OHM_BASE_URL; Authorization = OHM_API_KEY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
