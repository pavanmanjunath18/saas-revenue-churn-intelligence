-- ============================================================
-- 02_validate_analytics.sql
-- Data quality assertions for the analytics layer.
-- Every query should return 0 rows. Any non-zero result
-- indicates a bug in the analytics model logic.
-- ============================================================

\echo ''
\echo '=== Analytics Layer Validation ==='
\echo ''

-- ────────────────────────────────────────────────────────────
-- MRR MOVEMENT REPORT
-- ────────────────────────────────────────────────────────────
\echo '--- mrr_movement_report ---'

-- Every row must have a valid movement type
\echo 'CHECK: no null movement types'
SELECT 'null_movement_type' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE movement_type IS NULL;

-- MRR values must be non-negative
\echo 'CHECK: no negative MRR'
SELECT 'negative_mrr' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE current_mrr_cents < 0;

-- Churned rows must have current_mrr = 0
\echo 'CHECK: churned rows have zero current MRR'
SELECT 'churned_nonzero_mrr' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE movement_type = 'churned' AND current_mrr_cents != 0;

-- New/reactivation/expansion/contraction/unchanged must have current_mrr > 0
\echo 'CHECK: active movement types have positive MRR'
SELECT 'active_movement_zero_mrr' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE movement_type IN ('new','reactivation','expansion','contraction','unchanged')
  AND current_mrr_cents = 0;

-- Expansion must have positive mrr_change_cents
\echo 'CHECK: expansion has positive delta'
SELECT 'expansion_nonpositive_delta' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE movement_type = 'expansion' AND mrr_change_cents <= 0;

-- Contraction must have negative mrr_change_cents
\echo 'CHECK: contraction has negative delta'
SELECT 'contraction_nonnegative_delta' AS check_name, COUNT(*) AS violation_count
FROM analytics.mrr_movement_report
WHERE movement_type = 'contraction' AND mrr_change_cents >= 0;

-- Each customer should appear at most once per month
\echo 'CHECK: no duplicate customer-month rows'
SELECT 'duplicate_customer_month' AS check_name, COUNT(*) AS violation_count
FROM (
    SELECT customer_id, month, COUNT(*) AS cnt
    FROM analytics.mrr_movement_report
    GROUP BY customer_id, month
    HAVING COUNT(*) > 1
) dups;

-- ────────────────────────────────────────────────────────────
-- MONTHLY REVENUE OVERVIEW
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '--- monthly_revenue_overview ---'

-- No negative MRR components
\echo 'CHECK: no negative MRR components'
SELECT 'negative_mrr_component' AS check_name, COUNT(*) AS violation_count
FROM analytics.monthly_revenue_overview
WHERE new_mrr_usd < 0
   OR expansion_mrr_usd < 0
   OR contraction_mrr_usd < 0
   OR churned_mrr_usd < 0;

-- GRR should never exceed 100%
\echo 'CHECK: GRR <= 100'
SELECT 'grr_exceeds_100' AS check_name, COUNT(*) AS violation_count
FROM analytics.monthly_revenue_overview
WHERE grr_pct > 100.01;  -- tiny float tolerance

-- Active customers should be positive every month
\echo 'CHECK: positive active customer count every month'
SELECT 'zero_active_customers' AS check_name, COUNT(*) AS violation_count
FROM analytics.monthly_revenue_overview
WHERE active_customers = 0;

-- ────────────────────────────────────────────────────────────
-- COHORT RETENTION
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '--- cohort_retention ---'

-- Period 0 retention must be 100%
\echo 'CHECK: period 0 retention = 100%'
SELECT 'period_zero_not_100pct' AS check_name, COUNT(*) AS violation_count
FROM analytics.cohort_retention
WHERE period_number = 0 AND retention_pct != 100.00;

-- Retention must be between 0 and 100
\echo 'CHECK: retention pct in [0,100]'
SELECT 'retention_out_of_range' AS check_name, COUNT(*) AS violation_count
FROM analytics.cohort_retention
WHERE retention_pct < 0 OR retention_pct > 100.01;

-- Cohort sizes must be positive
\echo 'CHECK: positive cohort sizes'
SELECT 'zero_cohort_size' AS check_name, COUNT(*) AS violation_count
FROM analytics.cohort_retention
WHERE cohort_size <= 0;

-- ────────────────────────────────────────────────────────────
-- CUSTOMER HEALTH SCORES
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '--- customer_health_scores ---'

-- Health score must be 0-100
\echo 'CHECK: health score in [0,100]'
SELECT 'health_score_out_of_range' AS check_name, COUNT(*) AS violation_count
FROM analytics.customer_health_scores
WHERE health_score < 0 OR health_score > 100;

-- All component scores must be 0-100
\echo 'CHECK: component scores in [0,100]'
SELECT 'component_score_out_of_range' AS check_name, COUNT(*) AS violation_count
FROM analytics.customer_health_scores
WHERE usage_score   NOT BETWEEN 0 AND 100
   OR payment_score NOT BETWEEN 0 AND 100
   OR support_score NOT BETWEEN 0 AND 100
   OR tenure_score  NOT BETWEEN 0 AND 100
   OR feature_score NOT BETWEEN 0 AND 100;

-- No duplicate customers
\echo 'CHECK: one row per active customer'
SELECT 'duplicate_customer_health' AS check_name, COUNT(*) AS violation_count
FROM (
    SELECT customer_id, COUNT(*) AS cnt
    FROM analytics.customer_health_scores
    GROUP BY customer_id HAVING COUNT(*) > 1
) dups;

-- ────────────────────────────────────────────────────────────
-- CHURN RISK SEGMENTS
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '--- churn_risk_segments ---'

-- All risk tiers must be valid values
\echo 'CHECK: valid risk tiers'
SELECT 'invalid_risk_tier' AS check_name, COUNT(*) AS violation_count
FROM analytics.churn_risk_segments
WHERE risk_tier NOT IN ('critical','high','medium','low','champion');

-- Risk flag count must be 0–5
\echo 'CHECK: flag count in [0,5]'
SELECT 'invalid_flag_count' AS check_name, COUNT(*) AS violation_count
FROM analytics.churn_risk_segments
WHERE risk_flag_count NOT BETWEEN 0 AND 5;

-- ────────────────────────────────────────────────────────────
-- SUMMARY STATS
-- ────────────────────────────────────────────────────────────
\echo ''
\echo '=== Business Sanity Stats ==='

-- Movement type distribution
\echo ''
\echo 'MRR movement type distribution:'
SELECT
    movement_type,
    COUNT(*)                            AS row_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM analytics.mrr_movement_report
GROUP BY movement_type
ORDER BY row_count DESC;

-- Latest month revenue snapshot
\echo ''
\echo 'Latest month revenue snapshot:'
SELECT
    month,
    total_mrr_usd,
    arr_usd,
    active_customers,
    new_customers,
    churned_customers,
    nrr_pct,
    grr_pct,
    customer_churn_rate_pct
FROM analytics.monthly_revenue_overview
ORDER BY month DESC
LIMIT 3;

-- Health / risk distribution
\echo ''
\echo 'Churn risk distribution:'
SELECT
    risk_tier,
    COUNT(*)                            AS customers,
    ROUND(SUM(mrr_usd), 2)             AS mrr_usd,
    ROUND(SUM(mrr_at_risk_usd), 2)     AS mrr_at_risk_usd
FROM analytics.churn_risk_segments
GROUP BY risk_tier
ORDER BY
    CASE risk_tier
        WHEN 'critical' THEN 1
        WHEN 'high'     THEN 2
        WHEN 'medium'   THEN 3
        WHEN 'low'      THEN 4
        WHEN 'champion' THEN 5
    END;

-- Cohort retention sample (first 6 cohorts, periods 0/3/6/12)
\echo ''
\echo 'Cohort retention sample (periods 0, 3, 6, 12):'
SELECT
    cohort_month,
    cohort_size,
    MAX(CASE WHEN period_number = 0  THEN retention_pct END) AS "M0",
    MAX(CASE WHEN period_number = 3  THEN retention_pct END) AS "M3",
    MAX(CASE WHEN period_number = 6  THEN retention_pct END) AS "M6",
    MAX(CASE WHEN period_number = 12 THEN retention_pct END) AS "M12"
FROM analytics.cohort_retention
GROUP BY cohort_month, cohort_size
ORDER BY cohort_month
LIMIT 6;
