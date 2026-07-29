#!/usr/bin/env python3
"""Pack public doc URLs into markdown via Ohm compliant fetch."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

WATERMARK = "\n\n---\nvia withOhm — compliant fetch for agents · https://withohm.dev/i\n"


def pack(urls: list[str], *, base: str, api_key: str, purpose: str) -> str:
    body = {
        "model": "mock",
        "messages": [
            {
                "role": "user",
                "content": "Pack the fetched documentation into clear markdown context.",
            }
        ],
        "fetch_web_context": True,
        "web_purpose": purpose,
        "web_urls": urls,
        "web_format": "markdown",
        "web_compliance_ack": True,
        "terms_ack": True,
        "dpa_ack": True,
        "cache_control": "no_store",
    }
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # Prefer injected context echoes if present; else assistant content
    choices = data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        content = msg.get("content") or ""
        if content:
            return content.strip() + WATERMARK
    return json.dumps(data, indent=2) + WATERMARK


def main() -> int:
    p = argparse.ArgumentParser(description="docs-context-packer via withOhm")
    p.add_argument("urls", nargs="+", help="Public https documentation URLs")
    p.add_argument(
        "--purpose",
        default="public_web_retrieval",
        help="Ohm web_purpose",
    )
    args = p.parse_args()
    base = os.environ.get("OHM_BASE_URL", "https://api.withohm.dev/v1")
    key = os.environ.get("OHM_API_KEY", "")
    if not key or key.startswith("sk-at-REPLACE"):
        print(
            "Set OHM_API_KEY (https://withohm.dev/i). Compliant fetch for agents.",
            file=sys.stderr,
        )
        return 2
    try:
        print(pack(args.urls, base=base, api_key=key, purpose=args.purpose))
    except urllib.error.HTTPError as e:
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
