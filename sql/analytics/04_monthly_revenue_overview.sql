-- ============================================================
-- analytics.monthly_revenue_overview
-- One row per month. Aggregate MRR/ARR with full movement
-- breakdown (new, expansion, contraction, churn, reactivation)
-- plus NRR, GRR, and customer counts.
--
-- Depends on: analytics.mrr_movement_report (run 05 first)
--
-- Key metric definitions:
--   MRR       — sum of all active mrr_cents / 100
--   ARR       — MRR × 12
--   New MRR   — revenue from brand-new customers
--   Expansion — incremental revenue from upgrades
--   Contraction — lost revenue from downgrades (not churn)
--   Churned MRR — revenue lost to full cancellation
--   NRR       — (beginning_mrr + expansion - contraction - churn) / beginning_mrr × 100
--   GRR       — (beginning_mrr - contraction - churn) / beginning_mrr × 100
--               (always ≤ 100; excludes expansion)
-- ============================================================

CREATE MATERIALIZED VIEW analytics.monthly_revenue_overview AS
WITH

-- ── Aggregate movement components per month ──
monthly_components AS (
    SELECT
        month,

        -- Total active MRR (all customers paying this month)
        SUM(CASE WHEN current_mrr_cents > 0 THEN current_mrr_cents ELSE 0 END)
            AS total_mrr_cents,

        -- New MRR: first-ever revenue from a customer
        SUM(CASE WHEN movement_type = 'new'         THEN current_mrr_cents ELSE 0 END)
            AS new_mrr_cents,

        -- Expansion: incremental MRR from existing customers (delta only)
        SUM(CASE WHEN movement_type = 'expansion'   THEN mrr_change_cents  ELSE 0 END)
            AS expansion_mrr_cents,

        -- Contraction: MRR lost due to downgrade (absolute value of negative delta)
        SUM(CASE WHEN movement_type = 'contraction' THEN ABS(mrr_change_cents) ELSE 0 END)
            AS contraction_mrr_cents,

        -- Churned MRR: revenue lost to full cancellation (use prev_mrr, since current = 0)
        SUM(CASE WHEN movement_type = 'churned'     THEN prev_mrr_cents    ELSE 0 END)
            AS churned_mrr_cents,

        -- Reactivation MRR: revenue from returning customers
        SUM(CASE WHEN movement_type = 'reactivation' THEN current_mrr_cents ELSE 0 END)
            AS reactivation_mrr_cents,

        -- Beginning MRR = what existing (pre-month) customers were paying
        -- = prev_mrr of all customers who were active last month
        SUM(CASE WHEN movement_type IN ('unchanged','expansion','contraction','churned')
                 THEN prev_mrr_cents ELSE 0 END)
            AS beginning_mrr_cents,

        -- Customer counts
        COUNT(DISTINCT CASE WHEN current_mrr_cents > 0 THEN customer_id END)
            AS active_customers,
        COUNT(DISTINCT CASE WHEN movement_type = 'new'          THEN customer_id END)
            AS new_customers,
        COUNT(DISTINCT CASE WHEN movement_type = 'expansion'    THEN customer_id END)
            AS expansion_customers,
        COUNT(DISTINCT CASE WHEN movement_type = 'contraction'  THEN customer_id END)
            AS contraction_customers,
        COUNT(DISTINCT CASE WHEN movement_type = 'churned'      THEN customer_id END)
            AS churned_customers,
        COUNT(DISTINCT CASE WHEN movement_type = 'reactivation' THEN customer_id END)
            AS reactivation_customers

    FROM analytics.mrr_movement_report
    GROUP BY month
),

-- ── Segment-level MRR breakdown ──
segment_mrr AS (
    SELECT
        month,
        SUM(CASE WHEN segment = 'smb'         AND current_mrr_cents > 0 THEN current_mrr_cents ELSE 0 END)
            AS smb_mrr_cents,
        SUM(CASE WHEN segment = 'mid_market'  AND current_mrr_cents > 0 THEN current_mrr_cents ELSE 0 END)
            AS mid_market_mrr_cents,
        SUM(CASE WHEN segment = 'enterprise'  AND current_mrr_cents > 0 THEN current_mrr_cents ELSE 0 END)
            AS enterprise_mrr_cents
    FROM analytics.mrr_movement_report
    GROUP BY month
)

SELECT
    mc.month,

    -- ── MRR & ARR ──
    ROUND(mc.total_mrr_cents       / 100.0, 2)  AS total_mrr_usd,
    ROUND(mc.total_mrr_cents * 12  / 100.0, 2)  AS arr_usd,

    -- ── Movement components ──
    ROUND(mc.new_mrr_cents          / 100.0, 2)  AS new_mrr_usd,
    ROUND(mc.expansion_mrr_cents    / 100.0, 2)  AS expansion_mrr_usd,
    ROUND(mc.contraction_mrr_cents  / 100.0, 2)  AS contraction_mrr_usd,
    ROUND(mc.churned_mrr_cents      / 100.0, 2)  AS churned_mrr_usd,
    ROUND(mc.reactivation_mrr_cents / 100.0, 2)  AS reactivation_mrr_usd,

    -- Net new MRR = new + expansion + reactivation - contraction - churn
    ROUND((mc.new_mrr_cents + mc.expansion_mrr_cents + mc.reactivation_mrr_cents
           - mc.contraction_mrr_cents - mc.churned_mrr_cents) / 100.0, 2)
                                                  AS net_new_mrr_usd,

    -- ── Retention rates ──
    -- NRR: includes expansion (can exceed 100%)
    CASE WHEN mc.beginning_mrr_cents > 0
         THEN ROUND(100.0 *
              (mc.beginning_mrr_cents + mc.expansion_mrr_cents
               - mc.contraction_mrr_cents - mc.churned_mrr_cents)
              / mc.beginning_mrr_cents, 2)
         ELSE NULL
    END                                           AS nrr_pct,

    -- GRR: capped at 100% (no expansion credit)
    CASE WHEN mc.beginning_mrr_cents > 0
         THEN ROUND(100.0 *
              LEAST(mc.beginning_mrr_cents,
                    mc.beginning_mrr_cents - mc.contraction_mrr_cents - mc.churned_mrr_cents)
              / mc.beginning_mrr_cents, 2)
         ELSE NULL
    END                                           AS grr_pct,

    -- Churn rate: churned customers / beginning active customers
    CASE WHEN mc.active_customers + mc.churned_customers > 0
         THEN ROUND(100.0 * mc.churned_customers
                  / (mc.active_customers + mc.churned_customers), 2)
         ELSE NULL
    END                                           AS customer_churn_rate_pct,

    -- ── Customer counts ──
    mc.active_customers,
    mc.new_customers,
    mc.expansion_customers,
    mc.contraction_customers,
    mc.churned_customers,
    mc.reactivation_customers,

    -- ── Segment MRR ──
    ROUND(sm.smb_mrr_cents         / 100.0, 2)  AS smb_mrr_usd,
    ROUND(sm.mid_market_mrr_cents  / 100.0, 2)  AS mid_market_mrr_usd,
    ROUND(sm.enterprise_mrr_cents  / 100.0, 2)  AS enterprise_mrr_usd,

    -- ── Per-customer metrics ──
    CASE WHEN mc.active_customers > 0
         THEN ROUND(mc.total_mrr_cents / 100.0 / mc.active_customers, 2)
         ELSE NULL
    END                                           AS arpa_usd

FROM monthly_components mc
JOIN segment_mrr sm ON mc.month = sm.month
ORDER BY mc.month;

CREATE INDEX idx_monthly_rev_month ON analytics.monthly_revenue_overview(month);
