-- ============================================================
-- SaaS Revenue & Churn Intelligence Platform
-- Phase 2: Post-Load Validation Queries
--
-- Run after load_data.py to verify data integrity.
-- All queries return 0 rows if the check passes.
-- Non-zero rows = problem to investigate.
--
-- Usage:
--   psql $DATABASE_URL -f sql/schema/03_validation_queries.sql
-- ============================================================

SET search_path TO raw;

-- ────────────────────────────────────────────────────────────
-- SECTION 1: Row Counts
-- ────────────────────────────────────────────────────────────
\echo '=== Row Counts ==='

SELECT 'products'           AS table_name, COUNT(*) AS row_count FROM raw.products
UNION ALL SELECT 'plans',             COUNT(*) FROM raw.plans
UNION ALL SELECT 'customers',         COUNT(*) FROM raw.customers
UNION ALL SELECT 'discounts',         COUNT(*) FROM raw.discounts
UNION ALL SELECT 'subscriptions',     COUNT(*) FROM raw.subscriptions
UNION ALL SELECT 'subscription_items',COUNT(*) FROM raw.subscription_items
UNION ALL SELECT 'invoices',          COUNT(*) FROM raw.invoices
UNION ALL SELECT 'invoice_line_items',COUNT(*) FROM raw.invoice_line_items
UNION ALL SELECT 'payments',          COUNT(*) FROM raw.payments
UNION ALL SELECT 'refunds',           COUNT(*) FROM raw.refunds
UNION ALL SELECT 'product_usage',     COUNT(*) FROM raw.product_usage
UNION ALL SELECT 'support_tickets',   COUNT(*) FROM raw.support_tickets
ORDER BY table_name;

-- ────────────────────────────────────────────────────────────
-- SECTION 2: FK Integrity
-- All queries should return 0 rows.
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '=== FK Integrity (expect 0 rows each) ==='

\echo '-- Subscriptions with missing customer_id'
SELECT COUNT(*) AS orphan_count
FROM raw.subscriptions s
LEFT JOIN raw.customers c ON s.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

\echo '-- Invoices with missing customer_id'
SELECT COUNT(*) AS orphan_count
FROM raw.invoices i
LEFT JOIN raw.customers c ON i.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

\echo '-- Invoices with missing subscription_id'
SELECT COUNT(*) AS orphan_count
FROM raw.invoices i
LEFT JOIN raw.subscriptions s ON i.subscription_id = s.subscription_id
WHERE s.subscription_id IS NULL;

\echo '-- Payments with missing invoice_id'
SELECT COUNT(*) AS orphan_count
FROM raw.payments p
LEFT JOIN raw.invoices i ON p.invoice_id = i.invoice_id
WHERE i.invoice_id IS NULL;

\echo '-- Refunds with missing payment_id'
SELECT COUNT(*) AS orphan_count
FROM raw.refunds r
LEFT JOIN raw.payments p ON r.payment_id = p.payment_id
WHERE p.payment_id IS NULL;

\echo '-- Product usage with missing customer_id'
SELECT COUNT(*) AS orphan_count
FROM raw.product_usage u
LEFT JOIN raw.customers c ON u.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

\echo '-- Support tickets with missing customer_id'
SELECT COUNT(*) AS orphan_count
FROM raw.support_tickets t
LEFT JOIN raw.customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- ────────────────────────────────────────────────────────────
-- SECTION 3: Business Logic Checks
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '=== Business Logic (expect 0 rows each) ==='

\echo '-- Negative MRR'
SELECT subscription_id, mrr_cents
FROM raw.subscriptions
WHERE mrr_cents < 0;

\echo '-- Negative invoice totals'
SELECT invoice_id, total_cents
FROM raw.invoices
WHERE total_cents <= 0;

\echo '-- Canceled subscriptions missing canceled_at'
SELECT subscription_id, status, canceled_at
FROM raw.subscriptions
WHERE status = 'canceled'
  AND canceled_at IS NULL;

\echo '-- Subscriptions where canceled_at <= started_at'
SELECT subscription_id, started_at, canceled_at
FROM raw.subscriptions
WHERE canceled_at IS NOT NULL
  AND canceled_at <= started_at;

\echo '-- Invoices with billing_period_end before start'
SELECT invoice_id, billing_period_start, billing_period_end
FROM raw.invoices
WHERE billing_period_end < billing_period_start;

\echo '-- Payments referencing paid invoices but marked failed (data inconsistency)'
SELECT p.payment_id, p.status AS payment_status, i.status AS invoice_status
FROM raw.payments p
JOIN raw.invoices i ON p.invoice_id = i.invoice_id
WHERE i.status = 'paid'
  AND p.status = 'failed'
  AND NOT EXISTS (
      -- Allow: a failed attempt followed by a successful retry on the same invoice
      SELECT 1 FROM raw.payments p2
      WHERE p2.invoice_id = p.invoice_id
        AND p2.status = 'succeeded'
        AND p2.payment_id != p.payment_id
  )
LIMIT 20;

\echo '-- Product usage months not on first day of month'
SELECT usage_id, month
FROM raw.product_usage
WHERE EXTRACT(DAY FROM month) != 1;

-- ────────────────────────────────────────────────────────────
-- SECTION 4: Business Sanity Stats
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '=== Business Sanity Stats ==='

\echo '-- Active vs canceled subscriptions'
SELECT status, COUNT(*) AS count
FROM raw.subscriptions
GROUP BY status
ORDER BY count DESC;

\echo '-- MRR by segment (active subscriptions)'
SELECT
    c.segment,
    COUNT(DISTINCT s.customer_id)         AS active_customers,
    COUNT(s.subscription_id)              AS active_subs,
    SUM(s.mrr_cents) / 100                AS total_mrr_usd,
    AVG(s.mrr_cents) / 100                AS avg_mrr_usd
FROM raw.subscriptions s
JOIN raw.customers c ON s.customer_id = c.customer_id
WHERE s.status = 'active'
GROUP BY c.segment
ORDER BY total_mrr_usd DESC;

\echo '-- Total MRR and ARR'
SELECT
    SUM(mrr_cents) / 100        AS total_mrr_usd,
    SUM(mrr_cents) / 100 * 12   AS total_arr_usd,
    COUNT(DISTINCT customer_id) AS active_customers
FROM raw.subscriptions
WHERE status = 'active';

\echo '-- Invoice payment rate'
SELECT
    status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM raw.invoices
GROUP BY status
ORDER BY count DESC;

\echo '-- Customer count by segment'
SELECT segment, COUNT(*) AS customer_count
FROM raw.customers
GROUP BY segment
ORDER BY customer_count DESC;

\echo '-- Date range of data'
SELECT
    MIN(signup_date) AS first_signup,
    MAX(signup_date) AS last_signup
FROM raw.customers;

SELECT
    MIN(billing_period_start) AS first_invoice_month,
    MAX(billing_period_start) AS last_invoice_month
FROM raw.invoices;
