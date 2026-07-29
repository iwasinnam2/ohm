"""Signed Stripe webhook lifecycle against a live Ohm API host.

Uses admin issue + signed webhook events (checkout.session.completed then
customer.subscription.deleted) and asserts chat 403 after cancel.

Env:
  STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET (must match gateway)
  AT_ADMIN_API_KEY (or AT_ADMIN_API_KEYS first entry)
  OHM_BASE_URL (default https://api.withohm.dev)
  OHM_RESOLVE_IP (optional NLB IP for pre-DNS SNI via curl)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def _admin_key() -> str:
    key = (os.environ.get("AT_ADMIN_API_KEY") or "").strip()
    if key:
        return key
    keys = (os.environ.get("AT_ADMIN_API_KEYS") or "").strip()
    if keys:
        return keys.split(",")[0].strip()
    # bootstrap often shares AT_API_KEYS
    keys = (os.environ.get("AT_API_KEYS") or "").strip()
    if keys:
        return keys.split(",")[0].strip()
    raise SystemExit("Set AT_ADMIN_API_KEY or AT_ADMIN_API_KEYS")


def _curl_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: bytes | None = None,
    resolve_ip: str = "",
) -> tuple[int, str]:
    hdr_file = Path(os.environ.get("TEMP", ".")) / f"ohm_hdr_{os.getpid()}.txt"
    body_file = Path(os.environ.get("TEMP", ".")) / f"ohm_body_{os.getpid()}.txt"
    args = ["curl.exe", "-sS", "-D", str(hdr_file), "-o", str(body_file), "-X", method, "--max-time", "90"]
    if resolve_ip:
        # parse host/port from url
        from urllib.parse import urlparse

        u = urlparse(url)
        port = u.port or (443 if u.scheme == "https" else 80)
        args += ["--resolve", f"{u.hostname}:{port}:{resolve_ip}"]
    for k, v in headers.items():
        args += ["-H", f"{k}: {v}"]
    payload_path = None
    if body is not None:
        payload_path = Path(os.environ.get("TEMP", ".")) / f"ohm_payload_{os.getpid()}.bin"
        payload_path.write_bytes(body)
        args += ["--data-binary", f"@{payload_path}"]
    args.append(url)
    subprocess.check_call(args)
    raw_hdr = hdr_file.read_text(encoding="utf-8", errors="replace")
    status = 0
    for line in raw_hdr.splitlines():
        if line.startswith("HTTP/"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                status = int(parts[1])
    text = body_file.read_text(encoding="utf-8", errors="replace")
    for p in (hdr_file, body_file, payload_path):
        if p and p.exists():
            p.unlink(missing_ok=True)
    return status, text


def main() -> int:
    _load_dotenv()
    import stripe

    sk = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    whsec = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
    if not sk or not whsec:
        # Prefer cluster webhook secret file if local .env is stale
        tmp = ROOT / "scripts" / ".stripe_webhook_secret.tmp"
        if tmp.exists():
            whsec = tmp.read_text(encoding="utf-8").strip()
        if not sk or not whsec:
            raise SystemExit("Need STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET")

    stripe.api_key = sk
    base = (os.environ.get("OHM_BASE_URL") or "https://api.withohm.dev").rstrip("/")
    resolve_ip = (os.environ.get("OHM_RESOLVE_IP") or "").strip()
    admin = _admin_key()
    api_root = base if base.endswith("/v1") else f"{base}/v1"

    # 1) Issue tenant
    issue_body = json.dumps(
        {
            "label": f"stripe-life-{int(time.time())}",
            "plan": "payg",
            "terms_ack": True,
            "dpa_ack": True,
        }
    ).encode()
    code, text = _curl_json(
        "POST",
        f"{api_root}/admin/tenants",
        headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
        body=issue_body,
        resolve_ip=resolve_ip,
    )
    if code not in (200, 201):
        print(f"FAIL issue tenant {code}: {text}", file=sys.stderr)
        return 1
    issued = json.loads(text)
    api_key = issued["api_key"]
    tenant_id = issued["tenant"]["tenant_id"]
    print(f"OK: issued tenant={tenant_id}")

    # 2) Signed checkout.session.completed → active
    payload = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "client_reference_id": tenant_id,
                "customer": "cus_test_lifecycle",
                "subscription": "sub_test_lifecycle",
                "metadata": {"tenant_id": tenant_id, "plan": "payg"},
            }
        },
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    timestamp = int(time.time())
    import hashlib
    import hmac

    signed = hmac.new(
        whsec.encode(),
        f"{timestamp}.{raw.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    header = f"t={timestamp},v1={signed}"

    code, text = _curl_json(
        "POST",
        f"{api_root}/billing/webhook",
        headers={"Stripe-Signature": header, "Content-Type": "application/json"},
        body=raw,
        resolve_ip=resolve_ip,
    )
    if code != 200:
        print(f"FAIL webhook activate {code}: {text}", file=sys.stderr)
        return 1
    print("OK: webhook checkout.session.completed")

    chat_body = json.dumps(
        {"model": "mock", "messages": [{"role": "user", "content": "life-active"}]}
    ).encode()
    code, text = _curl_json(
        "POST",
        f"{api_root}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        body=chat_body,
        resolve_ip=resolve_ip,
    )
    if code != 200:
        print(f"FAIL chat while active {code}: {text}", file=sys.stderr)
        return 1
    print("OK: chat while active")

    # 3) Signed subscription.deleted → suspended → 403
    payload2 = {
        "id": f"evt_test_del_{int(time.time())}",
        "object": "event",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_lifecycle",
                "object": "subscription",
                "customer": "cus_test_lifecycle",
                "metadata": {"tenant_id": tenant_id, "plan": "payg"},
            }
        },
    }
    raw2 = json.dumps(payload2, separators=(",", ":")).encode()
    timestamp = int(time.time())
    signed = hmac.new(
        whsec.encode(),
        f"{timestamp}.{raw2.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    header2 = f"t={timestamp},v1={signed}"

    code, text = _curl_json(
        "POST",
        f"{api_root}/billing/webhook",
        headers={"Stripe-Signature": header2, "Content-Type": "application/json"},
        body=raw2,
        resolve_ip=resolve_ip,
    )
    if code != 200:
        print(f"FAIL webhook cancel {code}: {text}", file=sys.stderr)
        return 1
    print("OK: webhook customer.subscription.deleted")

    code, text = _curl_json(
        "POST",
        f"{api_root}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        body=chat_body,
        resolve_ip=resolve_ip,
    )
    if code != 403:
        print(f"FAIL expected 403 after cancel, got {code}: {text}", file=sys.stderr)
        return 1
    print("OK: chat 403 after cancel")
    print(f"Stripe webhook lifecycle passed against {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
