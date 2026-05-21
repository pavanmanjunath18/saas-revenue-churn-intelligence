-- ============================================================
-- analytics.customer_overview
-- One row per customer. Combines customer attributes with
-- their current subscription state and lifetime billing stats.
-- ============================================================

CREATE OR REPLACE VIEW analytics.customer_overview AS
WITH active_sub AS (
    -- Latest active subscription per customer (core product only for plan/MRR)
    SELECT DISTINCT ON (customer_id)
        customer_id,
        subscription_id,
        plan_id,
        billing_interval,
        mrr_cents,
        started_at AS subscription_started_at
    FROM raw.subscriptions
    WHERE status = 'active'
      AND product_id = '00000000-0000-0000-0000-000000000001'
    ORDER BY customer_id, started_at DESC
),
lifetime_billing AS (
    SELECT
        i.customer_id,
        COUNT(DISTINCT i.invoice_id)            AS total_invoices,
        SUM(i.total_cents)                      AS total_invoiced_cents,
        SUM(i.amount_paid_cents)                AS total_paid_cents,
        COUNT(CASE WHEN i.status != 'paid'
                   THEN 1 END)                  AS unpaid_invoices,
        MAX(i.billing_period_start)             AS last_invoice_month
    FROM raw.invoices i
    GROUP BY i.customer_id
),
sub_history AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(started_at))::date  AS first_subscription_month,
        DATE_TRUNC('month', MAX(started_at))::date  AS latest_subscription_month,
        -- How many distinct plans has this customer been on? (proxy for churn/upgrade count)
        COUNT(DISTINCT plan_id)                     AS distinct_plans_used,
        COUNT(*)                                    AS total_subscription_records,
        BOOL_OR(status = 'canceled')                AS ever_churned
    FROM raw.subscriptions
    GROUP BY customer_id
),
plan_info AS (
    SELECT plan_id, plan_name
    FROM raw.plans
)
SELECT
    c.customer_id,
    c.company_name,
    c.segment,
    c.industry,
    c.country,
    c.employee_count,
    c.signup_date,
    c.acquired_channel,

    -- Subscription state
    sh.first_subscription_month,
    sh.latest_subscription_month,
    p.plan_name                                         AS current_plan,
    asub.billing_interval                               AS current_billing_interval,
    asub.mrr_cents                                      AS current_mrr_cents,
    ROUND(asub.mrr_cents / 100.0, 2)                    AS current_mrr_usd,
    CASE WHEN asub.customer_id IS NOT NULL
         THEN TRUE ELSE FALSE END                       AS is_active,

    -- Tenure
    DATE_PART('month',
        AGE(CURRENT_DATE, sh.first_subscription_month::date)
    )::int                                              AS tenure_months,

    -- Subscription history
    sh.total_subscription_records,
    sh.distinct_plans_used,
    sh.ever_churned,

    -- Lifetime billing
    lb.total_invoices,
    ROUND(lb.total_invoiced_cents / 100.0, 2)           AS total_invoiced_usd,
    ROUND(lb.total_paid_cents     / 100.0, 2)           AS total_paid_usd,
    lb.unpaid_invoices,
    lb.last_invoice_month

FROM raw.customers c
LEFT JOIN sub_history  sh   ON c.customer_id = sh.customer_id
LEFT JOIN active_sub   asub ON c.customer_id = asub.customer_id
LEFT JOIN plan_info    p    ON asub.plan_id   = p.plan_id
LEFT JOIN lifetime_billing lb ON c.customer_id = lb.customer_id
WHERE c.is_deleted = FALSE;
