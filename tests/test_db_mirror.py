"""DB mirror writer: gating + idempotent SQL (fake connection, no live Postgres)."""
from __future__ import annotations

from at_utility.config import Settings
from at_utility.db import mirror


class FakeCursor:
    def __init__(self, calls: list):
        self._calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._calls.append((sql, params))


class FakeConn:
    def __init__(self):
        self.calls: list = []
        self.commits = 0

    def cursor(self):
        return FakeCursor(self.calls)

    def commit(self):
        self.commits += 1


def test_mirror_enabled_gating():
    assert mirror.mirror_enabled(Settings(ohm_db_enabled=False, database_url="")) is False
    assert mirror.mirror_enabled(Settings(ohm_db_enabled=True, database_url="")) is False
    assert mirror.mirror_enabled(Settings(ohm_db_enabled=False, database_url="postgres://x")) is False
    assert mirror.mirror_enabled(Settings(ohm_db_enabled=True, database_url="postgres://x")) is True


def test_upsert_account_is_idempotent_upsert():
    conn = FakeConn()
    rec = {
        "tenant_id": "tenant_x", "plan": "payg", "status": "active",
        "key_prefix": "sk-at-abc", "created_at": 123, "stripe_customer_id": "cus_x",
    }
    mirror.upsert_account(conn, rec)
    sql, params = conn.calls[0]
    assert "INSERT INTO accounts" in sql
    assert "ON CONFLICT (tenant_id) DO UPDATE SET" in sql
    assert "updated_at = now()" in sql
    assert params[0] == "tenant_x"
    assert len(params) == len(mirror._ACCOUNT_COLUMNS)
    assert conn.commits == 1


def test_upsert_account_coerces_not_null_defaults():
    conn = FakeConn()
    # Partial dict omitting the NOT NULL columns -> must not send NULL for them.
    mirror.upsert_account(conn, {"tenant_id": "tenant_x", "plan": "payg", "status": "active"})
    _sql, params = conn.calls[0]
    row = dict(zip(mirror._ACCOUNT_COLUMNS, params))
    assert row["billing_paid"] is False
    assert row["soft_quota_usd"] == 0
    assert row["request_cap"] == 0


def test_record_usage_daily_upsert():
    conn = FakeConn()
    mirror.record_usage_daily(
        conn, "tenant_x", "2026-07-30",
        {"cache_hit_tokens": 10, "cache_miss_tokens": 5, "requests": 2, "revenue_usd": 0.01},
    )
    sql, params = conn.calls[0]
    assert "INSERT INTO usage_daily" in sql
    assert "ON CONFLICT (tenant_id, day) DO UPDATE SET" in sql
    assert params[0] == "tenant_x" and params[1] == "2026-07-30"


def test_append_billing_event_serializes_raw():
    conn = FakeConn()
    mirror.append_billing_event(conn, {
        "tenant_id": "tenant_x", "event_type": "invoice.paid",
        "stripe_customer_id": "cus_x", "status": "paid", "raw": {"id": "in_1"},
    })
    sql, params = conn.calls[0]
    assert "INSERT INTO billing_events" in sql
    assert params[1] == "invoice.paid"
    assert params[-1] == '{"id": "in_1"}'  # raw JSON-encoded


def test_ensure_schema_executes_ddl():
    conn = FakeConn()
    mirror.ensure_schema(conn)
    sql, _ = conn.calls[0]
    assert "CREATE TABLE IF NOT EXISTS accounts" in sql
    assert "CREATE TABLE IF NOT EXISTS usage_daily" in sql
    assert "CREATE TABLE IF NOT EXISTS billing_events" in sql
    assert conn.commits == 1


def test_account_projection_from_tenant_record():
    from dataclasses import asdict
    from at_utility.tenants import TenantRecord

    rec = TenantRecord(
        tenant_id="tenant_y", plan="payg", status="active",
        key_prefix="sk-at-xyz", created_at=1, stripe_customer_id="cus_y",
    )
    acct = mirror.account_from_tenant_record(asdict(rec), region="local", label="demo")
    assert acct["tenant_id"] == "tenant_y"
    assert acct["region"] == "local" and acct["label"] == "demo"
    assert set(acct) == set(mirror._ACCOUNT_COLUMNS)
