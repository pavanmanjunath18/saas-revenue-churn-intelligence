-- ============================================================
-- analytics.customer_health_scores
-- Composite health score (0–100) for every active customer.
-- Refreshed as a materialized view so it can be indexed.
--
-- Component weights (match Python generator for consistency):
--   usage_trend    30% — recent session/API activity vs prior 3 months
--   payment_health 25% — invoice payment rate (last 6 months of data)
--   support_calm   20% — absence of recent high-severity open tickets
--   tenure         15% — months active (longer = more stable)
--   feature_depth  10% — breadth of features used recently
--
-- Reference point: MAX(month) in product_usage (avoids CURRENT_DATE
-- falling outside the simulated data range).
-- ============================================================

CREATE MATERIALIZED VIEW analytics.customer_health_scores AS
WITH

-- ── Reference date anchored to latest data ──
ref AS (
    SELECT MAX(month) AS latest_month FROM raw.product_usage
),

-- ── Active core product subscriptions ──
active_subs AS (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        subscription_id,
        plan_id,
        billing_interval,
        mrr_cents,
        started_at
    FROM raw.subscriptions
    WHERE status = 'active'
      AND product_id = '00000000-0000-0000-0000-000000000001'
    ORDER BY customer_id, started_at DESC
),

-- ── Usage trend: recent 3 months vs prior 3 months ──
usage_recent AS (
    SELECT
        pu.customer_id,
        AVG(pu.sessions_count + pu.api_calls / 10.0)   AS recent_activity,
        AVG(pu.features_used_count)                     AS recent_features
    FROM raw.product_usage pu
    CROSS JOIN ref
    WHERE pu.month > (ref.latest_month - INTERVAL '3 months')
    GROUP BY pu.customer_id
),
usage_prior AS (
    SELECT
        pu.customer_id,
        AVG(pu.sessions_count + pu.api_calls / 10.0)   AS prior_activity
    FROM raw.product_usage pu
    CROSS JOIN ref
    WHERE pu.month > (ref.latest_month - INTERVAL '6 months')
      AND pu.month <= (ref.latest_month - INTERVAL '3 months')
    GROUP BY pu.customer_id
),

-- ── Payment health: last 6 months of invoice data ──
payment_health AS (
    SELECT
        i.customer_id,
        COUNT(*)                                            AS total_invoices,
        COUNT(CASE WHEN i.status NOT IN ('paid','void')
                   THEN 1 END)                             AS unpaid_invoices
    FROM raw.invoices i
    CROSS JOIN ref
    WHERE i.billing_period_start > (ref.latest_month - INTERVAL '6 months')
    GROUP BY i.customer_id
),

-- ── Support: open high/critical tickets in last 90 days of data ──
support_health AS (
    SELECT
        st.customer_id,
        COUNT(CASE WHEN st.priority IN ('high','critical')
                    AND st.status NOT IN ('resolved','closed')
                   THEN 1 END)                             AS open_critical_tickets,
        COUNT(CASE WHEN st.priority IN ('high','critical') THEN 1 END)
                                                           AS total_high_priority_tickets,
        COUNT(*)                                           AS recent_ticket_count
    FROM raw.support_tickets st
    CROSS JOIN ref
    WHERE st.opened_at > (ref.latest_month - INTERVAL '90 days')::timestamptz
    GROUP BY st.customer_id
),

-- ── Compute individual component scores (0–100) ──
scored AS (
    SELECT
        ac.customer_id,
        ac.subscription_id,
        ac.plan_id,
        ac.billing_interval,
        ac.mrr_cents,
        ac.started_at,

        -- Usage trend score (30%)
        LEAST(100, GREATEST(0,
            CASE
                WHEN ur.recent_activity IS NULL              THEN 20
                WHEN up.prior_activity  IS NULL
                  OR up.prior_activity  = 0
                  AND ur.recent_activity > 0                 THEN 65
                WHEN up.prior_activity  = 0                  THEN 30
                WHEN ur.recent_activity >= up.prior_activity THEN
                    LEAST(100, 75 + 25 * LEAST(1.0,
                        (ur.recent_activity / up.prior_activity) - 1.0))
                ELSE
                    GREATEST(0, 75 * (ur.recent_activity / NULLIF(up.prior_activity, 0)))
            END
        ))::numeric                                           AS usage_score,

        -- Payment health score (25%)
        LEAST(100, GREATEST(0,
            CASE WHEN COALESCE(ph.total_invoices, 0) = 0 THEN 80
                 ELSE 100 - 100 * COALESCE(ph.unpaid_invoices, 0)
                           / ph.total_invoices
            END
        ))::numeric                                           AS payment_score,

        -- Support calm score (20%)
        LEAST(100, GREATEST(0,
            100
            - 25 * COALESCE(sh.open_critical_tickets,       0)
            - 10 * COALESCE(sh.total_high_priority_tickets, 0)
            -  3 * COALESCE(sh.recent_ticket_count,         0)
        ))::numeric                                           AS support_score,

        -- Tenure score (15%): ~5 pts/month, capped at 100 at 20 months
        LEAST(100, GREATEST(0,
            5 * DATE_PART('month', AGE(
                (SELECT latest_month FROM ref),
                ac.started_at::date
            ))
        ))::numeric                                           AS tenure_score,

        -- Feature depth score (10%): up to 5 distinct feature types
        LEAST(100, GREATEST(0,
            COALESCE(ur.recent_features, 0) * 20
        ))::numeric                                           AS feature_score

    FROM active_subs ac
    LEFT JOIN usage_recent  ur ON ac.customer_id = ur.customer_id
    LEFT JOIN usage_prior   up ON ac.customer_id = up.customer_id
    LEFT JOIN payment_health ph ON ac.customer_id = ph.customer_id
    LEFT JOIN support_health sh ON ac.customer_id = sh.customer_id
)

SELECT
    s.customer_id,
    c.company_name,
    c.segment,
    c.industry,
    pl.plan_name,
    s.billing_interval,
    ROUND(s.mrr_cents / 100.0, 2)                          AS mrr_usd,

    -- Component scores
    ROUND(s.usage_score,   1)                              AS usage_score,
    ROUND(s.payment_score, 1)                              AS payment_score,
    ROUND(s.support_score, 1)                              AS support_score,
    ROUND(s.tenure_score,  1)                              AS tenure_score,
    ROUND(s.feature_score, 1)                              AS feature_score,

    -- Composite health score
    ROUND(
        0.30 * s.usage_score   +
        0.25 * s.payment_score +
        0.20 * s.support_score +
        0.15 * s.tenure_score  +
        0.10 * s.feature_score,
    1)                                                     AS health_score,

    -- Months on platform
    DATE_PART('month', AGE(
        (SELECT latest_month FROM ref),
        s.started_at::date
    ))::int                                                AS tenure_months

FROM scored s
JOIN raw.customers c  ON s.customer_id = c.customer_id
LEFT JOIN raw.plans pl ON s.plan_id    = pl.plan_id
ORDER BY health_score DESC;

CREATE INDEX idx_health_customer ON analytics.customer_health_scores(customer_id);
CREATE INDEX idx_health_score    ON analytics.customer_health_scores(health_score);
CREATE INDEX idx_health_segment  ON analytics.customer_health_scores(segment);
