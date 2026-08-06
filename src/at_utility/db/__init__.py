"""Optional durable system-of-record mirror (Postgres/Neon).

Redis remains the hot path and real-time source of truth; this package holds a
queryable mirror of account details, daily usage rollups, and a billing-event log
so accounts can be categorised, reported on, and reconciled.

Inert unless ``OHM_DB_ENABLED=true`` and ``DATABASE_URL`` are set. The Postgres
driver (``psycopg``) is imported lazily so importing this package never requires
the ``[db]`` extra.
"""

from at_utility.db.mirror import (
    append_billing_event,
    connect,
    ensure_schema,
    mirror_enabled,
    record_usage_daily,
    upsert_account,
)

__all__ = [
    "append_billing_event",
    "connect",
    "ensure_schema",
    "mirror_enabled",
    "record_usage_daily",
    "upsert_account",
]
