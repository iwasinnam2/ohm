-- withOhm system-of-record mirror (Postgres/Neon).
-- Redis stays authoritative for real-time; these tables hold queryable history.
-- Epoch fields mirror TenantRecord ints (seconds) to avoid tz-conversion drift.

-- Identity + billing/subscription category.
CREATE TABLE IF NOT EXISTS accounts (
    tenant_id                TEXT PRIMARY KEY,
    plan                     TEXT NOT NULL,
    status                   TEXT NOT NULL,
    key_prefix               TEXT,
    region                   TEXT,
    label                    TEXT,
    created_at               BIGINT,
    expires_at               BIGINT,
    stripe_customer_id       TEXT,
    stripe_subscription_id   TEXT,
    billing_paid             BOOLEAN NOT NULL DEFAULT FALSE,
    billing_delinquent_since BIGINT,
    soft_quota_usd           NUMERIC NOT NULL DEFAULT 0,
    request_cap              BIGINT NOT NULL DEFAULT 0,
    terms_version            TEXT,
    dpa_version              TEXT,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts (status);
CREATE INDEX IF NOT EXISTS idx_accounts_plan ON accounts (plan);
CREATE INDEX IF NOT EXISTS idx_accounts_stripe_customer ON accounts (stripe_customer_id);

-- Usage/metering category (time-series rollup, one row per tenant per UTC day).
CREATE TABLE IF NOT EXISTS usage_daily (
    tenant_id         TEXT NOT NULL,
    day               DATE NOT NULL,
    cache_hit_tokens  NUMERIC NOT NULL DEFAULT 0,
    cache_miss_tokens NUMERIC NOT NULL DEFAULT 0,
    fetches           NUMERIC NOT NULL DEFAULT 0,
    requests          NUMERIC NOT NULL DEFAULT 0,
    revenue_usd       NUMERIC NOT NULL DEFAULT 0,
    cache_hit_ratio   NUMERIC NOT NULL DEFAULT 0,
    synced_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, day)
);
CREATE INDEX IF NOT EXISTS idx_usage_daily_day ON usage_daily (day);

-- Compliance/audit category (append-only billing-event log).
CREATE TABLE IF NOT EXISTS billing_events (
    id                     BIGSERIAL PRIMARY KEY,
    tenant_id              TEXT,
    event_type             TEXT NOT NULL,
    stripe_customer_id     TEXT,
    stripe_subscription_id TEXT,
    status                 TEXT,
    received_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw                    JSONB
);
CREATE INDEX IF NOT EXISTS idx_billing_events_tenant ON billing_events (tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_type ON billing_events (event_type);
