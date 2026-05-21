-- ============================================================
-- SaaS Revenue & Churn Intelligence Platform
-- Phase 2: Schema DDL
--
-- Creates the `raw` schema and all 12 tables with:
--   - Primary keys
--   - Foreign keys
--   - CHECK constraints on categoricals
--   - Indexes on high-cardinality filter columns
--
-- Run: psql $DATABASE_URL -f sql/schema/01_create_schema.sql
-- ============================================================

-- Drop and recreate schema for clean reloads
DROP SCHEMA IF EXISTS raw CASCADE;
CREATE SCHEMA raw;

SET search_path TO raw;

-- ────────────────────────────────────────────────────────────
-- PRODUCTS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.products (
    product_id    UUID         PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL,
    product_type  VARCHAR(50)  NOT NULL CHECK (product_type IN ('core','add_on','professional_services')),
    description   TEXT,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- PLANS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.plans (
    plan_id           UUID         PRIMARY KEY,
    product_id        UUID         NOT NULL REFERENCES raw.products(product_id),
    plan_name         VARCHAR(100) NOT NULL,
    billing_interval  VARCHAR(20)  NOT NULL CHECK (billing_interval IN ('monthly','annual','one_time')),
    price_cents       INTEGER      NOT NULL CHECK (price_cents >= 0),
    max_seats         INTEGER,                -- NULL = unlimited
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_plans_product_id ON raw.plans(product_id);

-- ────────────────────────────────────────────────────────────
-- CUSTOMERS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.customers (
    customer_id       UUID         PRIMARY KEY,
    company_name      VARCHAR(255) NOT NULL,
    industry          VARCHAR(100),
    segment           VARCHAR(50)  NOT NULL CHECK (segment IN ('smb','mid_market','enterprise')),
    employee_count    INTEGER      CHECK (employee_count > 0),
    country           VARCHAR(100),
    city              VARCHAR(100),
    signup_date       DATE         NOT NULL,
    acquired_channel  VARCHAR(100),
    account_owner     VARCHAR(200),
    is_deleted        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ  NOT NULL,
    updated_at        TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_customers_segment    ON raw.customers(segment);
CREATE INDEX idx_customers_signup     ON raw.customers(signup_date);
CREATE INDEX idx_customers_industry   ON raw.customers(industry);

-- ────────────────────────────────────────────────────────────
-- DISCOUNTS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.discounts (
    discount_id    UUID          PRIMARY KEY,
    customer_id    UUID          NOT NULL REFERENCES raw.customers(customer_id),
    coupon_code    VARCHAR(100),
    discount_type  VARCHAR(50)   NOT NULL CHECK (discount_type IN ('percentage','fixed_amount')),
    discount_value NUMERIC(10,2) NOT NULL CHECK (discount_value > 0),
    duration       VARCHAR(50)   NOT NULL CHECK (duration IN ('once','repeating','forever')),
    duration_months INTEGER,
    valid_from     DATE,
    valid_until    DATE,
    created_at     TIMESTAMPTZ   NOT NULL
);

CREATE INDEX idx_discounts_customer ON raw.discounts(customer_id);

-- ────────────────────────────────────────────────────────────
-- SUBSCRIPTIONS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.subscriptions (
    subscription_id   UUID        PRIMARY KEY,
    customer_id       UUID        NOT NULL REFERENCES raw.customers(customer_id),
    product_id        UUID        NOT NULL REFERENCES raw.products(product_id),
    plan_id           UUID        NOT NULL REFERENCES raw.plans(plan_id),
    status            VARCHAR(50) NOT NULL CHECK (status IN ('active','canceled','past_due','paused','trialing')),
    billing_interval  VARCHAR(20) NOT NULL CHECK (billing_interval IN ('monthly','annual','one_time')),
    started_at        DATE        NOT NULL,
    canceled_at       DATE,
    trial_ends_at     DATE,
    seats             INTEGER     NOT NULL DEFAULT 1 CHECK (seats > 0),
    mrr_cents         INTEGER     NOT NULL CHECK (mrr_cents >= 0),
    discount_id       UUID        REFERENCES raw.discounts(discount_id),
    created_at        TIMESTAMPTZ NOT NULL,
    updated_at        TIMESTAMPTZ NOT NULL,

    CONSTRAINT chk_cancel_after_start
        CHECK (canceled_at IS NULL OR canceled_at > started_at)
);

CREATE INDEX idx_subs_customer_id ON raw.subscriptions(customer_id);
CREATE INDEX idx_subs_plan_id     ON raw.subscriptions(plan_id);
CREATE INDEX idx_subs_product_id  ON raw.subscriptions(product_id);
CREATE INDEX idx_subs_status      ON raw.subscriptions(status);
CREATE INDEX idx_subs_started_at  ON raw.subscriptions(started_at);

-- ────────────────────────────────────────────────────────────
-- SUBSCRIPTION_ITEMS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.subscription_items (
    item_id             UUID        PRIMARY KEY,
    subscription_id     UUID        NOT NULL REFERENCES raw.subscriptions(subscription_id),
    plan_id             UUID        NOT NULL REFERENCES raw.plans(plan_id),
    quantity            INTEGER     NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price_cents    INTEGER     NOT NULL CHECK (unit_price_cents >= 0),
    total_price_cents   INTEGER     NOT NULL CHECK (total_price_cents >= 0),
    started_at          DATE        NOT NULL,
    ended_at            DATE,
    created_at          TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_sub_items_subscription ON raw.subscription_items(subscription_id);

-- ────────────────────────────────────────────────────────────
-- INVOICES
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.invoices (
    invoice_id              UUID        PRIMARY KEY,
    customer_id             UUID        NOT NULL REFERENCES raw.customers(customer_id),
    subscription_id         UUID        NOT NULL REFERENCES raw.subscriptions(subscription_id),
    invoice_number          VARCHAR(50) NOT NULL UNIQUE,
    status                  VARCHAR(50) NOT NULL CHECK (status IN ('draft','open','paid','void','uncollectible')),
    billing_period_start    DATE        NOT NULL,
    billing_period_end      DATE        NOT NULL,
    subtotal_cents          INTEGER     NOT NULL CHECK (subtotal_cents >= 0),
    discount_amount_cents   INTEGER     NOT NULL DEFAULT 0 CHECK (discount_amount_cents >= 0),
    tax_cents               INTEGER     NOT NULL DEFAULT 0 CHECK (tax_cents >= 0),
    total_cents             INTEGER     NOT NULL CHECK (total_cents > 0),
    amount_paid_cents       INTEGER     NOT NULL DEFAULT 0 CHECK (amount_paid_cents >= 0),
    amount_due_cents        INTEGER     NOT NULL DEFAULT 0 CHECK (amount_due_cents >= 0),
    issued_at               TIMESTAMPTZ NOT NULL,
    due_at                  TIMESTAMPTZ,
    paid_at                 TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL,

    CONSTRAINT chk_period_order
        CHECK (billing_period_end >= billing_period_start)
);

CREATE INDEX idx_invoices_customer      ON raw.invoices(customer_id);
CREATE INDEX idx_invoices_subscription  ON raw.invoices(subscription_id);
CREATE INDEX idx_invoices_status        ON raw.invoices(status);
CREATE INDEX idx_invoices_period_start  ON raw.invoices(billing_period_start);

-- ────────────────────────────────────────────────────────────
-- INVOICE_LINE_ITEMS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.invoice_line_items (
    line_item_id         UUID        PRIMARY KEY,
    invoice_id           UUID        NOT NULL REFERENCES raw.invoices(invoice_id),
    subscription_item_id UUID        REFERENCES raw.subscription_items(item_id),
    description          TEXT,
    quantity             INTEGER     NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price_cents     INTEGER     NOT NULL CHECK (unit_price_cents >= 0),
    amount_cents         INTEGER     NOT NULL CHECK (amount_cents >= 0),
    created_at           TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_line_items_invoice ON raw.invoice_line_items(invoice_id);

-- ────────────────────────────────────────────────────────────
-- PAYMENTS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.payments (
    payment_id      UUID         PRIMARY KEY,
    invoice_id      UUID         NOT NULL REFERENCES raw.invoices(invoice_id),
    customer_id     UUID         NOT NULL REFERENCES raw.customers(customer_id),
    amount_cents    INTEGER      NOT NULL CHECK (amount_cents > 0),
    currency        VARCHAR(10)  NOT NULL DEFAULT 'USD',
    status          VARCHAR(50)  NOT NULL CHECK (status IN ('succeeded','failed','pending','refunded')),
    payment_method  VARCHAR(50)  CHECK (payment_method IN ('card','ach','wire','check','other')),
    failure_reason  VARCHAR(255),
    attempted_at    TIMESTAMPTZ  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_payments_invoice   ON raw.payments(invoice_id);
CREATE INDEX idx_payments_customer  ON raw.payments(customer_id);
CREATE INDEX idx_payments_status    ON raw.payments(status);

-- ────────────────────────────────────────────────────────────
-- REFUNDS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.refunds (
    refund_id    UUID         PRIMARY KEY,
    payment_id   UUID         NOT NULL REFERENCES raw.payments(payment_id),
    customer_id  UUID         NOT NULL REFERENCES raw.customers(customer_id),
    amount_cents INTEGER      NOT NULL CHECK (amount_cents > 0),
    reason       VARCHAR(255),
    status       VARCHAR(50)  NOT NULL CHECK (status IN ('pending','succeeded','failed')),
    issued_at    TIMESTAMPTZ  NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_refunds_payment  ON raw.refunds(payment_id);
CREATE INDEX idx_refunds_customer ON raw.refunds(customer_id);

-- ────────────────────────────────────────────────────────────
-- PRODUCT_USAGE
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.product_usage (
    usage_id             UUID    PRIMARY KEY,
    customer_id          UUID    NOT NULL REFERENCES raw.customers(customer_id),
    product_id           UUID    NOT NULL REFERENCES raw.products(product_id),
    month                DATE    NOT NULL,  -- always first day of month
    active_users         INTEGER CHECK (active_users >= 0),
    sessions_count       INTEGER CHECK (sessions_count >= 0),
    features_used_count  INTEGER CHECK (features_used_count >= 0),
    api_calls            INTEGER CHECK (api_calls >= 0),
    data_exported_mb     NUMERIC(12,2),
    report_views         INTEGER CHECK (report_views >= 0),
    created_at           TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_usage_customer_product_month
        UNIQUE (customer_id, product_id, month)
);

CREATE INDEX idx_usage_customer ON raw.product_usage(customer_id);
CREATE INDEX idx_usage_month    ON raw.product_usage(month);
CREATE INDEX idx_usage_product  ON raw.product_usage(product_id);

-- ────────────────────────────────────────────────────────────
-- SUPPORT_TICKETS
-- ────────────────────────────────────────────────────────────
CREATE TABLE raw.support_tickets (
    ticket_id               UUID        PRIMARY KEY,
    customer_id             UUID        NOT NULL REFERENCES raw.customers(customer_id),
    category                VARCHAR(100) CHECK (category IN ('billing','technical','feature_request','onboarding','account')),
    priority                VARCHAR(50)  CHECK (priority IN ('low','medium','high','critical')),
    status                  VARCHAR(50)  CHECK (status IN ('open','in_progress','resolved','closed')),
    subject                 TEXT,
    opened_at               TIMESTAMPTZ NOT NULL,
    resolved_at             TIMESTAMPTZ,
    resolution_time_hours   NUMERIC(10,2),
    csat_score              SMALLINT     CHECK (csat_score BETWEEN 1 AND 5),
    created_at              TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_tickets_customer  ON raw.support_tickets(customer_id);
CREATE INDEX idx_tickets_priority  ON raw.support_tickets(priority);
CREATE INDEX idx_tickets_opened_at ON raw.support_tickets(opened_at);
