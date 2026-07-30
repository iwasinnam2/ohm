"""Local Section-B go-live smoke: Stripe billing lifecycle behaviors.

Exercises the billing behaviors that don't need a live Stripe account by
HMAC-signing webhook events with ``STRIPE_WEBHOOK_SECRET`` (must match the
running gateway). Cross-platform (stdlib only). Requires the gateway, Redis,
and the ingest worker to be running.

Checks:
  1. checkout.session.completed -> tenant active
  2. invoice.paid resolves the tenant by stripe_customer_id (reverse index)
  3. daily web-fetch soft-cap -> 429 fetch_cap_day, lifted after invoice.paid
  4. delinquency: invoice.payment_failed -> web fetch 402 (chat still 200)
  5. cancel (customer.subscription.deleted) -> all calls 403
  6. metering ledger moves on cache miss + hit

Gateway config for a full green run:
  STRIPE_WEBHOOK_SECRET=<any value>            # must match this script's env/.env
  AT_FREE_TIER_FETCH_CAP_DAY=<small, e.g. 1>   # so the soft-cap check can trip

Env for this script:
  OHM_BASE_URL   (default http://127.0.0.1:8080)
  STRIPE_WEBHOOK_SECRET (required; read from env or repo .env)
  AT_ADMIN_API_KEY / AT_ADMIN_API_KEYS / AT_API_KEYS  (admin bearer; default sk-at-dev)
  OHM_FETCH_CAP  (default 1; set equal to the gateway AT_FREE_TIER_FETCH_CAP_DAY)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
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
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _admin_key() -> str:
    for name in ("AT_ADMIN_API_KEY", "AT_ADMIN_API_KEYS", "AT_API_KEYS"):
        val = (os.environ.get(name) or "").strip()
        if val:
            return val.split(",")[0].strip()
    return "sk-at-dev"


def _http(method: str, url: str, *, headers: dict | None = None, data: bytes | None = None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


class Smoke:
    def __init__(self) -> None:
        self.base = (os.environ.get("OHM_BASE_URL") or "http://127.0.0.1:8080").rstrip("/")
        self.api_root = self.base if self.base.endswith("/v1") else f"{self.base}/v1"
        self.admin = _admin_key()
        self.whsec = (os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip()
        self.cap = int(os.environ.get("OHM_FETCH_CAP", "1"))
        self.results: list[tuple[str, bool, str]] = []

    def rec(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))

    def issue(self, label: str) -> tuple[str, str]:
        body = json.dumps(
            {"plan": "payg", "label": label, "terms_ack": True, "dpa_ack": True}
        ).encode()
        code, text = _http(
            "POST",
            f"{self.api_root}/admin/tenants",
            headers={"Authorization": f"Bearer {self.admin}", "Content-Type": "application/json"},
            data=body,
        )
        if code not in (200, 201):
            raise SystemExit(f"admin issue failed {code}: {text}")
        d = json.loads(text)
        return d["api_key"], d["tenant"]["tenant_id"]

    def webhook(self, event_type: str, obj: dict) -> tuple[int, str]:
        payload = {
            "id": f"evt_{int(time.time()*1000)}",
            "object": "event",
            "type": event_type,
            "data": {"object": obj},
        }
        raw = json.dumps(payload, separators=(",", ":")).encode()
        ts = int(time.time())
        sig = hmac.new(self.whsec.encode(), f"{ts}.{raw.decode()}".encode(), hashlib.sha256).hexdigest()
        return _http(
            "POST",
            f"{self.api_root}/billing/webhook",
            headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
            data=raw,
        )

    def chat(self, key: str, *, fetch: bool = False, urls: list[str] | None = None) -> tuple[int, str]:
        body: dict = {"model": "mock", "messages": [{"role": "user", "content": f"hi-{time.time()}"}]}
        if fetch:
            body.update({"fetch_web_context": True, "web_purpose": "public_web_retrieval", "web_urls": urls or []})
        return _http(
            "POST",
            f"{self.api_root}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            data=json.dumps(body).encode(),
        )

    def usage(self, key: str) -> dict:
        _, text = _http("GET", f"{self.api_root}/usage", headers={"Authorization": f"Bearer {key}"})
        return json.loads(text)

    def run(self) -> int:
        if not self.whsec:
            raise SystemExit("STRIPE_WEBHOOK_SECRET is required (must match the gateway).")

        # 1) checkout lifecycle -> active + 2) reverse-index resolve via invoice.paid
        key_a, ten_a = self.issue("secB-A")
        cus_a = f"cus_A_{int(time.time())}"
        code, text = self.webhook(
            "checkout.session.completed",
            {"id": "cs_A", "client_reference_id": ten_a, "customer": cus_a,
             "subscription": "sub_A", "metadata": {"tenant_id": ten_a, "plan": "payg"}},
        )
        self.rec("checkout.session.completed -> 200", code == 200, text[:120])
        code, text = self.webhook("invoice.paid", {"id": "in_A", "customer": cus_a, "subscription": "sub_A"})
        self.rec("invoice.paid resolves tenant by stripe_customer_id", code == 200, text[:120])
        code, _ = self.chat(key_a)
        self.rec("chat active after checkout -> 200", code == 200)

        # 3) daily fetch soft-cap -> 429, lifted after invoice.paid
        key_b, ten_b = self.issue("secB-B")
        over_cap_urls = [f"https://example.com/?n={i}" for i in range(self.cap + 1)]
        code, text = self.chat(key_b, fetch=True, urls=over_cap_urls)
        capped = code == 429 and json.loads(text).get("error", {}).get("code") == "fetch_cap_day"
        self.rec("unpaid payg fetch over soft-cap -> 429 fetch_cap_day", capped,
                 f"status={code} (cap={self.cap})")
        cus_b = f"cus_B_{int(time.time())}"
        self.webhook("checkout.session.completed",
                     {"id": "cs_B", "client_reference_id": ten_b, "customer": cus_b,
                      "subscription": "sub_B", "metadata": {"tenant_id": ten_b, "plan": "payg"}})
        self.webhook("invoice.paid", {"id": "in_B", "customer": cus_b, "subscription": "sub_B"})
        code, _ = self.chat(key_b, fetch=True, urls=["https://example.com"])
        self.rec("after invoice.paid fetch cap lifted -> not 429", code != 429, f"status={code}")

        # 4) delinquency: payment_failed -> fetch 402 (chat still 200); 5) cancel -> 403
        key_c, ten_c = self.issue("secB-C")
        cus_c = f"cus_C_{int(time.time())}"
        self.webhook("checkout.session.completed",
                     {"id": "cs_C", "client_reference_id": ten_c, "customer": cus_c,
                      "subscription": "sub_C", "metadata": {"tenant_id": ten_c, "plan": "payg"}})
        self.webhook("invoice.payment_failed", {"id": "in_C", "customer": cus_c, "subscription": "sub_C"})
        code, _ = self.chat(key_c)
        self.rec("delinquent: plain chat still 200", code == 200)
        code, text = self.chat(key_c, fetch=True, urls=["https://example.com"])
        d402 = code == 402 and json.loads(text).get("error", {}).get("code") == "billing_delinquent"
        self.rec("delinquent: web fetch blocked -> 402 billing_delinquent", d402, f"status={code}")
        self.webhook("customer.subscription.deleted",
                     {"id": "sub_C", "customer": cus_c, "metadata": {"tenant_id": ten_c}})
        code, _ = self.chat(key_c)
        self.rec("after cancel -> all calls 403", code == 403, f"status={code}")

        # 6) metering ledger moves on miss + hit
        fixed = json.dumps({"model": "mock", "messages": [{"role": "user", "content": "meter-probe"}]}).encode()
        hdrs = {"Authorization": f"Bearer {key_a}", "Content-Type": "application/json"}
        _http("POST", f"{self.api_root}/chat/completions", headers=hdrs, data=fixed)  # miss
        _http("POST", f"{self.api_root}/chat/completions", headers=hdrs, data=fixed)  # hit
        u = self.usage(key_a)
        self.rec(
            "metering: miss+hit recorded (requests>0, revenue>0, hit_ratio>0)",
            u["requests"] > 0 and u["revenue_usd"] > 0 and u["cache_hit_ratio"] > 0,
            f"requests={u['requests']} revenue={u['revenue_usd']:.6f} "
            f"hit_ratio={u['cache_hit_ratio']:.2f} stripe_synced={u['stripe_synced']}",
        )

        passed = sum(1 for _, ok, _ in self.results if ok)
        print(f"\n{passed}/{len(self.results)} checks passed")
        return 0 if passed == len(self.results) else 1


def main() -> int:
    _load_dotenv()
    return Smoke().run()


if __name__ == "__main__":
    raise SystemExit(main())
