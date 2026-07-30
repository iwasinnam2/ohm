"""Write API for the optional Postgres/Neon system-of-record mirror.

Functions take a DBAPI connection (``psycopg`` in production) so they are trivially
unit-testable with a fake connection. All writes are idempotent upserts keyed on the
natural key, so a reconciler can replay them safely.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from at_utility.config import Settings

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_ACCOUNT_COLUMNS = (
    "tenant_id",
    "plan",
    "status",
    "key_prefix",
    "region",
    "label",
    "created_at",
    "expires_at",
    "stripe_customer_id",
    "stripe_subscription_id",
    "billing_paid",
    "billing_delinquent_since",
    "soft_quota_usd",
    "request_cap",
    "terms_version",
    "dpa_version",
)

_USAGE_COLUMNS = (
    "cache_hit_tokens",
    "cache_miss_tokens",
    "fetches",
    "requests",
    "revenue_usd",
    "cache_hit_ratio",
)

# NOT NULL columns whose SQL DEFAULT only applies when omitted — never when an
# explicit NULL is sent. Coerce missing values so partial dicts don't error.
_ACCOUNT_NOT_NULL_DEFAULTS = {
    "billing_paid": False,
    "soft_quota_usd": 0,
    "request_cap": 0,
}


def mirror_enabled(settings: Settings) -> bool:
    return bool(settings.ohm_db_enabled and settings.database_url)


def connect(settings: Settings):
    """Open a psycopg connection. Raises a clear error if the [db] extra is missing."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Postgres mirror requires psycopg: pip install -e '.[db]'"
        ) from exc
    return psycopg.connect(settings.database_url)


def schema_sql() -> str:
    return _SCHEMA_PATH.read_text(encoding="utf-8")


def ensure_schema(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(schema_sql())
    conn.commit()


def upsert_account(conn: Any, record: dict[str, Any]) -> None:
    """Idempotent upsert of a TenantRecord-shaped dict into ``accounts``."""
    cols = list(_ACCOUNT_COLUMNS)
    values = []
    for c in cols:
        v = record.get(c)
        if v is None and c in _ACCOUNT_NOT_NULL_DEFAULTS:
            v = _ACCOUNT_NOT_NULL_DEFAULTS[c]
        values.append(v)
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "tenant_id")
    sql = (
        f"INSERT INTO accounts ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (tenant_id) DO UPDATE SET {updates}, updated_at = now()"
    )
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


def record_usage_daily(
    conn: Any, tenant_id: str, day: str, metrics: dict[str, Any]
) -> None:
    """Idempotent upsert of one tenant/day usage rollup into ``usage_daily``."""
    cols = ["tenant_id", "day", *(_USAGE_COLUMNS)]
    values = [tenant_id, day, *[metrics.get(c, 0) for c in _USAGE_COLUMNS]]
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in _USAGE_COLUMNS)
    sql = (
        f"INSERT INTO usage_daily ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (tenant_id, day) DO UPDATE SET {updates}, synced_at = now()"
    )
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


def append_billing_event(conn: Any, event: dict[str, Any]) -> None:
    """Append a webhook-derived event to the ``billing_events`` audit log."""
    sql = (
        "INSERT INTO billing_events "
        "(tenant_id, event_type, stripe_customer_id, stripe_subscription_id, status, raw) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    values = [
        event.get("tenant_id"),
        event.get("event_type"),
        event.get("stripe_customer_id"),
        event.get("stripe_subscription_id"),
        event.get("status"),
        json.dumps(event.get("raw")) if event.get("raw") is not None else None,
    ]
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


def account_from_tenant_record(record: dict[str, Any], *, region: str = "", label: str = "") -> dict[str, Any]:
    """Project a TenantRecord dict (asdict) into the accounts column set."""
    out = {c: record.get(c) for c in _ACCOUNT_COLUMNS}
    if region and not out.get("region"):
        out["region"] = region
    if label and not out.get("label"):
        out["label"] = label
    return out
