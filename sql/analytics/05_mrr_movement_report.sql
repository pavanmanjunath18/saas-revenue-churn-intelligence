-- ============================================================
-- analytics.mrr_movement_report
-- THE CORE MODEL. One row per customer per month for every
-- month where something happened (new, expansion, contraction,
-- churn, reactivation, unchanged). Rows where a customer was
-- never active are excluded.
--
-- Movement type definitions:
--   new          — first month with revenue (no prior history)
--   expansion    — MRR increased month-over-month
--   contraction  — MRR decreased month-over-month (still >0)
--   churned      — MRR dropped to 0 (was >0 last month)
--   reactivation — MRR came back after a 0-MRR month
--   unchanged    — active, same MRR as prior month
--
-- Only core product (product_id = 00000000-0000-0000-0000-000000000001)
-- ============================================================

CREATE MATERIALIZED VIEW analytics.mrr_movement_report AS
WITH

-- ── 1. Month spine: all months in the subscription dataset ──
months AS (
    SELECT generate_series(
        DATE_TRUNC('month', MIN(started_at))::date,
        DATE_TRUNC('month', COALESCE(MAX(canceled_at), '2025-12-01'::date))::date,
        '1 month'::interval
    )::date AS month
    FROM raw.subscriptions
    WHERE product_id = '00000000-0000-0000-0000-000000000001'
),

-- ── 2. All customers who ever had a core product subscription ──
core_customers AS (
    SELECT DISTINCT customer_id
    FROM raw.subscriptions
    WHERE product_id = '00000000-0000-0000-0000-000000000001'
),

-- ── 3. Full customer × month spine ──
spine AS (
    SELECT cc.customer_id, m.month
    FROM core_customers cc
    CROSS JOIN months m
),

-- ── 4. Active MRR per customer per month ──
-- A subscription is "active" in month M if:
--   started_at < first day of M+1  AND  (canceled_at IS NULL OR canceled_at >= first day of M)
active_mrr AS (
    SELECT DISTINCT ON (s.customer_id, m.month)
        s.customer_id,
        m.month,
        s.subscription_id,
        s.plan_id,
        s.mrr_cents,
        s.seats
    FROM raw.subscriptions s
    JOIN months m ON
        s.started_at <  (m.month + INTERVAL '1 month')::date
        AND (s.canceled_at IS NULL OR s.canceled_at >= m.month)
    WHERE s.product_id = '00000000-0000-0000-0000-000000000001'
    ORDER BY s.customer_id, m.month, s.started_at DESC
),

-- ── 5. First active month per customer (used to trim spine) ──
first_active AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(started_at))::date AS first_month
    FROM raw.subscriptions
    WHERE product_id = '00000000-0000-0000-0000-000000000001'
    GROUP BY customer_id
),

-- ── 6. Join spine with active MRR; only from each customer's first month ──
monthly_mrr AS (
    SELECT
        sp.customer_id,
        sp.month,
        COALESCE(am.subscription_id, NULL)      AS subscription_id,
        COALESCE(am.plan_id, NULL)              AS plan_id,
        COALESCE(am.mrr_cents, 0)               AS mrr_cents,
        am.seats
    FROM spine sp
    JOIN first_active fa ON sp.customer_id = fa.customer_id
    LEFT JOIN active_mrr am ON sp.customer_id = am.customer_id AND sp.month = am.month
    WHERE sp.month >= fa.first_month
),

-- ── 7. Add previous month's MRR via LAG ──
mrr_with_lag AS (
    SELECT
        customer_id,
        month,
        subscription_id,
        plan_id,
        mrr_cents                                                               AS current_mrr_cents,
        LAG(mrr_cents) OVER (PARTITION BY customer_id ORDER BY month)          AS prev_mrr_cents,
        seats
    FROM monthly_mrr
),

-- ── 8. Classify movement ──
classified AS (
    SELECT
        customer_id,
        month,
        subscription_id,
        plan_id,
        current_mrr_cents,
        COALESCE(prev_mrr_cents, 0)                                             AS prev_mrr_cents,
        current_mrr_cents - COALESCE(prev_mrr_cents, 0)                        AS mrr_change_cents,
        seats,
        CASE
            -- First ever active month (no prior row for this customer in spine)
            WHEN prev_mrr_cents IS NULL     AND current_mrr_cents > 0  THEN 'new'
            -- Coming back after a churned gap
            WHEN COALESCE(prev_mrr_cents, 0) = 0  AND current_mrr_cents > 0
             AND prev_mrr_cents IS NOT NULL                              THEN 'reactivation'
            -- Was active, now gone
            WHEN COALESCE(prev_mrr_cents, 0) > 0  AND current_mrr_cents = 0  THEN 'churned'
            -- Active both months: MRR went up
            WHEN prev_mrr_cents > 0 AND current_mrr_cents > prev_mrr_cents    THEN 'expansion'
            -- Active both months: MRR went down (but still >0)
            WHEN prev_mrr_cents > 0 AND current_mrr_cents < prev_mrr_cents    THEN 'contraction'
            -- Active both months: same MRR
            WHEN prev_mrr_cents > 0 AND current_mrr_cents = prev_mrr_cents    THEN 'unchanged'
            -- Both 0: customer not yet active, or months after final churn → exclude
            ELSE NULL
        END                                                                     AS movement_type
    FROM mrr_with_lag
)

-- ── 9. Final output: join with dimension tables ──
SELECT
    cl.customer_id,
    c.company_name,
    c.segment,
    c.industry,
    cl.month,
    cl.subscription_id,
    pl.plan_name,
    cl.current_mrr_cents,
    ROUND(cl.current_mrr_cents / 100.0, 2)      AS current_mrr_usd,
    cl.prev_mrr_cents,
    ROUND(cl.prev_mrr_cents    / 100.0, 2)      AS prev_mrr_usd,
    cl.mrr_change_cents,
    ROUND(cl.mrr_change_cents  / 100.0, 2)      AS mrr_change_usd,
    cl.movement_type,
    cl.seats
FROM classified cl
JOIN raw.customers c ON cl.customer_id = c.customer_id
LEFT JOIN raw.plans pl ON cl.plan_id = pl.plan_id
WHERE cl.movement_type IS NOT NULL
ORDER BY cl.month, cl.customer_id;

CREATE INDEX idx_mrr_movement_month          ON analytics.mrr_movement_report(month);
CREATE INDEX idx_mrr_movement_customer_month ON analytics.mrr_movement_report(customer_id, month);
CREATE INDEX idx_mrr_movement_type           ON analytics.mrr_movement_report(movement_type);
CREATE INDEX idx_mrr_movement_segment        ON analytics.mrr_movement_report(segment);
