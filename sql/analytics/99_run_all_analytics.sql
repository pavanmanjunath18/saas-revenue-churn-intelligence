-- ============================================================
-- 99_run_all_analytics.sql
-- Creates the analytics schema and runs all models in
-- dependency order. Safe to re-run: views are replaced,
-- materialized views are dropped and recreated.
--
-- Run order:
--   1. Schema creation
--   2. Views (no deps on other analytics models): 01, 02, 03
--   3. Core materialized view: 05 (mrr_movement_report)
--   4. Dependent materialized views: 04, 06, 07
--   5. Dependent on 07: 08 (churn_risk_segments)
-- ============================================================

-- ── Schema ──
CREATE SCHEMA IF NOT EXISTS analytics;

-- ── Drop materialized views (must happen before recreating dependencies) ──
DROP MATERIALIZED VIEW IF EXISTS analytics.churn_risk_segments      CASCADE;
DROP MATERIALIZED VIEW IF EXISTS analytics.customer_health_scores   CASCADE;
DROP MATERIALIZED VIEW IF EXISTS analytics.cohort_retention         CASCADE;
DROP MATERIALIZED VIEW IF EXISTS analytics.monthly_revenue_overview CASCADE;
DROP MATERIALIZED VIEW IF EXISTS analytics.mrr_movement_report      CASCADE;

\echo ''
\echo '=== Analytics Schema Build ==='
\echo ''

-- ── 01: customer_overview (VIEW) ──
\echo '01 customer_overview...'
\i sql/analytics/01_customer_overview.sql
\echo '   OK'

-- ── 02: subscription_details (VIEW) ──
\echo '02 subscription_details...'
\i sql/analytics/02_subscription_details.sql
\echo '   OK'

-- ── 03: invoice_details (VIEW) ──
\echo '03 invoice_details...'
\i sql/analytics/03_invoice_details.sql
\echo '   OK'

-- ── 05: mrr_movement_report (MATERIALIZED VIEW — core model) ──
\echo '05 mrr_movement_report...'
\i sql/analytics/05_mrr_movement_report.sql
\echo '   OK'

-- ── 04: monthly_revenue_overview (depends on 05) ──
\echo '04 monthly_revenue_overview...'
\i sql/analytics/04_monthly_revenue_overview.sql
\echo '   OK'

-- ── 06: cohort_retention ──
\echo '06 cohort_retention...'
\i sql/analytics/06_cohort_retention.sql
\echo '   OK'

-- ── 07: customer_health_scores ──
\echo '07 customer_health_scores...'
\i sql/analytics/07_customer_health_scores.sql
\echo '   OK'

-- ── 08: churn_risk_segments (depends on 07) ──
\echo '08 churn_risk_segments...'
\i sql/analytics/08_churn_risk_segments.sql
\echo '   OK'

\echo ''
\echo '=== Build complete. Row counts: ==='
\echo ''

SELECT
    schemaname,
    matviewname AS object_name,
    'MATERIALIZED VIEW' AS object_type
FROM pg_matviews
WHERE schemaname = 'analytics'

UNION ALL

SELECT
    schemaname,
    viewname AS object_name,
    'VIEW' AS object_type
FROM pg_views
WHERE schemaname = 'analytics'

ORDER BY object_type, object_name;

\echo ''
SELECT 'mrr_movement_report'      AS model, COUNT(*) AS rows FROM analytics.mrr_movement_report
UNION ALL
SELECT 'monthly_revenue_overview'       , COUNT(*)          FROM analytics.monthly_revenue_overview
UNION ALL
SELECT 'cohort_retention'               , COUNT(*)          FROM analytics.cohort_retention
UNION ALL
SELECT 'customer_health_scores'         , COUNT(*)          FROM analytics.customer_health_scores
UNION ALL
SELECT 'churn_risk_segments'            , COUNT(*)          FROM analytics.churn_risk_segments
ORDER BY model;
