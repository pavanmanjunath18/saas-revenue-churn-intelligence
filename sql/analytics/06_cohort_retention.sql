-- ============================================================
-- analytics.cohort_retention
-- Monthly cohort retention matrix. For each signup cohort,
-- tracks what % of customers are still active at periods 0–24.
--
-- period_number = 0 is the cohort's first active month (100%).
-- period_number = N is N months after cohort_month.
-- A customer is "retained" in month M if they have an active
-- core product subscription that covers month M.
-- ============================================================

CREATE MATERIALIZED VIEW analytics.cohort_retention AS
WITH

-- ── 1. Cohort assignment: first month a customer was active ──
cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(started_at))::date AS cohort_month
    FROM raw.subscriptions
    WHERE product_id = '00000000-0000-0000-0000-000000000001'
    GROUP BY customer_id
),

-- ── 2. Month spine ──
months AS (
    SELECT generate_series(
        DATE_TRUNC('month', MIN(started_at))::date,
        DATE_TRUNC('month', COALESCE(MAX(canceled_at), '2025-12-01'::date))::date,
        '1 month'::interval
    )::date AS month
    FROM raw.subscriptions
    WHERE product_id = '00000000-0000-0000-0000-000000000001'
),

-- ── 3. Active months per customer ──
customer_active_months AS (
    SELECT DISTINCT
        s.customer_id,
        m.month AS active_month
    FROM raw.subscriptions s
    JOIN months m ON
        s.started_at <  (m.month + INTERVAL '1 month')::date
        AND (s.canceled_at IS NULL OR s.canceled_at >= m.month)
    WHERE s.product_id = '00000000-0000-0000-0000-000000000001'
),

-- ── 4. Join cohort × activity → period number ──
cohort_activity AS (
    SELECT
        c.cohort_month,
        cam.customer_id,
        cam.active_month,
        -- How many months after cohort_month is this active_month?
        (DATE_PART('year',  cam.active_month) - DATE_PART('year',  c.cohort_month)) * 12
        + (DATE_PART('month', cam.active_month) - DATE_PART('month', c.cohort_month))
            AS period_number
    FROM cohorts c
    JOIN customer_active_months cam ON c.customer_id = cam.customer_id
    WHERE cam.active_month >= c.cohort_month
),

-- ── 5. Cohort sizes (period 0 = 100% denominator) ──
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)

SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.period_number,
    COUNT(DISTINCT ca.customer_id)                          AS retained_customers,
    ROUND(100.0 * COUNT(DISTINCT ca.customer_id)
          / cs.cohort_size, 2)                             AS retention_pct,
    ca.active_month                                         AS calendar_month
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
GROUP BY ca.cohort_month, cs.cohort_size, ca.period_number, ca.active_month
ORDER BY ca.cohort_month, ca.period_number;

CREATE INDEX idx_cohort_ret_cohort_month ON analytics.cohort_retention(cohort_month);
CREATE INDEX idx_cohort_ret_period       ON analytics.cohort_retention(period_number);
