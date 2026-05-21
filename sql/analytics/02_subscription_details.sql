-- ============================================================
-- analytics.subscription_details
-- One row per subscription. Enriched with customer, product,
-- and plan context. Useful for cohort and revenue analysis.
-- ============================================================

CREATE OR REPLACE VIEW analytics.subscription_details AS
WITH sub_sequence AS (
    -- Rank subscriptions per customer chronologically to detect upgrades/downgrades
    SELECT
        subscription_id,
        customer_id,
        plan_id,
        mrr_cents,
        started_at,
        canceled_at,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY started_at)    AS sub_rank,
        LAG(mrr_cents) OVER (PARTITION BY customer_id ORDER BY started_at)  AS prev_mrr_cents,
        LAG(plan_id)   OVER (PARTITION BY customer_id ORDER BY started_at)  AS prev_plan_id
    FROM raw.subscriptions
)
SELECT
    s.subscription_id,
    s.customer_id,
    c.company_name,
    c.segment,
    c.industry,

    -- Product & plan
    pr.product_name,
    pr.product_type,
    pl.plan_name,
    s.billing_interval,
    s.status,

    -- Dates
    s.started_at,
    s.canceled_at,
    COALESCE(s.canceled_at, CURRENT_DATE)           AS effective_end_date,

    -- Duration
    CASE
        WHEN s.canceled_at IS NOT NULL THEN
            DATE_PART('month', AGE(s.canceled_at::date, s.started_at::date))::int
        ELSE
            DATE_PART('month', AGE(CURRENT_DATE, s.started_at::date))::int
    END                                             AS duration_months,

    -- Revenue
    s.mrr_cents,
    ROUND(s.mrr_cents / 100.0, 2)                   AS mrr_usd,
    s.seats,

    -- Movement context (first sub per customer = new, else upgrade/downgrade/reactivation)
    ss.sub_rank,
    CASE
        WHEN ss.sub_rank = 1                            THEN 'new_customer'
        WHEN ss.prev_mrr_cents IS NULL                  THEN 'new_customer'
        WHEN s.mrr_cents > ss.prev_mrr_cents            THEN 'upgrade'
        WHEN s.mrr_cents < ss.prev_mrr_cents            THEN 'downgrade'
        WHEN s.mrr_cents = ss.prev_mrr_cents            THEN 'reactivation'
        ELSE 'other'
    END                                             AS subscription_type,

    s.discount_id,
    d.discount_type,
    d.discount_value,
    d.duration                                      AS discount_duration

FROM raw.subscriptions  s
JOIN raw.customers      c  ON s.customer_id = c.customer_id
JOIN raw.products       pr ON s.product_id  = pr.product_id
JOIN raw.plans          pl ON s.plan_id     = pl.plan_id
LEFT JOIN sub_sequence  ss ON s.subscription_id = ss.subscription_id
LEFT JOIN raw.discounts d  ON s.discount_id = d.discount_id;
