-- ============================================================
-- analytics.churn_risk_segments
-- Risk tier classification for every active customer.
-- Depends on analytics.customer_health_scores (run 07 first).
--
-- Risk tiers:
--   critical  — health_score < 30  (immediate intervention)
--   high      — health_score 30–49 (proactive outreach)
--   medium    — health_score 50–69 (monitor closely)
--   low       — health_score 70–84 (healthy, light touch)
--   champion  — health_score ≥ 85  (upsell / reference candidate)
--
-- Leading indicator flags explain WHY a customer is at risk.
-- ============================================================

CREATE MATERIALIZED VIEW analytics.churn_risk_segments AS
WITH

-- ── Flag-level risk signals ──
risk_signals AS (
    SELECT
        hs.customer_id,
        hs.company_name,
        hs.segment,
        hs.industry,
        hs.plan_name,
        hs.billing_interval,
        hs.mrr_usd,
        hs.health_score,
        hs.usage_score,
        hs.payment_score,
        hs.support_score,
        hs.tenure_score,
        hs.feature_score,
        hs.tenure_months,

        -- Risk tier
        CASE
            WHEN hs.health_score <  30  THEN 'critical'
            WHEN hs.health_score <  50  THEN 'high'
            WHEN hs.health_score <  70  THEN 'medium'
            WHEN hs.health_score <  85  THEN 'low'
            ELSE                             'champion'
        END                                                  AS risk_tier,

        -- Leading indicator flags
        hs.usage_score   < 40                                AS flag_usage_declining,
        hs.payment_score < 60                                AS flag_payment_issues,
        hs.support_score < 50                                AS flag_support_overloaded,
        hs.feature_score < 30                                AS flag_low_feature_adoption,
        hs.tenure_months < 3                                 AS flag_new_customer_risk,

        -- Revenue at risk
        CASE
            WHEN hs.health_score < 50
            THEN hs.mrr_usd
            ELSE 0
        END                                                  AS mrr_at_risk_usd

    FROM analytics.customer_health_scores hs
)

SELECT
    rs.customer_id,
    rs.company_name,
    rs.segment,
    rs.industry,
    rs.plan_name,
    rs.billing_interval,
    rs.mrr_usd,
    rs.health_score,
    rs.risk_tier,

    -- Count of active risk flags
    (   rs.flag_usage_declining::int
      + rs.flag_payment_issues::int
      + rs.flag_support_overloaded::int
      + rs.flag_low_feature_adoption::int
      + rs.flag_new_customer_risk::int
    )                                                        AS risk_flag_count,

    -- Individual flags
    rs.flag_usage_declining,
    rs.flag_payment_issues,
    rs.flag_support_overloaded,
    rs.flag_low_feature_adoption,
    rs.flag_new_customer_risk,

    -- Component scores for drill-down
    rs.usage_score,
    rs.payment_score,
    rs.support_score,
    rs.tenure_score,
    rs.feature_score,
    rs.tenure_months,

    rs.mrr_at_risk_usd,

    -- Recommended action
    CASE rs.risk_tier
        WHEN 'critical' THEN 'Immediate CSM escalation — potential churn within 30 days'
        WHEN 'high'     THEN 'Schedule executive business review this month'
        WHEN 'medium'   THEN 'CSM check-in + feature adoption guidance'
        WHEN 'low'      THEN 'Quarterly review — look for expansion opportunity'
        WHEN 'champion' THEN 'Upsell / case study / referral candidate'
    END                                                      AS recommended_action

FROM risk_signals rs
ORDER BY rs.health_score ASC, rs.mrr_usd DESC;

CREATE INDEX idx_risk_tier       ON analytics.churn_risk_segments(risk_tier);
CREATE INDEX idx_risk_customer   ON analytics.churn_risk_segments(customer_id);
CREATE INDEX idx_risk_score      ON analytics.churn_risk_segments(health_score);
CREATE INDEX idx_risk_segment    ON analytics.churn_risk_segments(segment);
