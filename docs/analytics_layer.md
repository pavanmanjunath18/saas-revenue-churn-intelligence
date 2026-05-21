# Analytics Layer — SaaS Revenue & Churn Intelligence Platform

## Overview

The `analytics` schema contains 8 models (3 VIEWs + 5 MATERIALIZED VIEWs) built on the `raw` schema. All models were validated against live data and passed 23 data quality assertions.

**As of Phase 3 completion (2025-12 data):**

| Model | Rows | Type |
|---|---|---|
| `customer_overview` | 1,500 | VIEW |
| `subscription_details` | ~2,394 | VIEW |
| `invoice_details` | ~10,495 | VIEW |
| `mrr_movement_report` | 12,607 | MATERIALIZED VIEW |
| `monthly_revenue_overview` | 24 | MATERIALIZED VIEW |
| `cohort_retention` | 300 | MATERIALIZED VIEW |
| `customer_health_scores` | 1,108 | MATERIALIZED VIEW |
| `churn_risk_segments` | 1,108 | MATERIALIZED VIEW |

---

## Model Reference

### `analytics.customer_overview` (VIEW)

One row per customer. Joins customer attributes with their current subscription state and lifetime billing stats. Excludes deleted customers.

**Key columns:** `customer_id`, `company_name`, `segment`, `is_active`, `current_mrr_usd`, `current_plan`, `tenure_months`, `total_invoiced_usd`, `ever_churned`

**Use for:** customer lists, account health snapshots, CSM tooling

---

### `analytics.subscription_details` (VIEW)

One row per subscription. Enriched with customer, product, plan, and movement context.

**Key columns:** `subscription_id`, `subscription_type` (`new_customer` / `upgrade` / `downgrade` / `reactivation`), `duration_months`, `mrr_usd`, `discount_type`

**Movement logic:** Uses `ROW_NUMBER` and `LAG(mrr_cents)` over subscriptions ordered by `started_at` per customer.

**Use for:** upgrade/downgrade analysis, discount attribution

---

### `analytics.invoice_details` (VIEW)

One row per invoice with customer, subscription, plan, and payment attempt context.

**Key columns:** `invoice_status`, `total_usd`, `amount_paid_usd`, `amount_due_usd`, `is_paid`, `days_to_pay`, `failed_payment_attempts`

**Use for:** AR analysis, dunning workflows, payment failure investigation

---

### `analytics.mrr_movement_report` (MATERIALIZED VIEW) ⭐ Core Model

**The most important model.** One row per customer per month, but only for months where a meaningful event occurred. Rows for inactive customers with no history are excluded.

#### Movement Type Definitions

| Type | Condition |
|---|---|
| `new` | First month with MRR — no prior subscription history |
| `expansion` | MRR increased month-over-month (customer still active) |
| `contraction` | MRR decreased month-over-month (customer still active) |
| `churned` | MRR dropped to 0 (was >0 last month) |
| `reactivation` | MRR came back after a 0-MRR gap month |
| `unchanged` | Active both months, same MRR |

#### SQL Pattern (core logic)

```sql
-- Month spine × active subscriptions
active_mrr AS (
    SELECT DISTINCT ON (s.customer_id, m.month) ...
    FROM raw.subscriptions s
    JOIN months m ON
        s.started_at < (m.month + INTERVAL '1 month')::date
        AND (s.canceled_at IS NULL OR s.canceled_at >= m.month)
),
-- LAG to get previous month's MRR
mrr_with_lag AS (
    SELECT ...,
        LAG(mrr_cents) OVER (PARTITION BY customer_id ORDER BY month) AS prev_mrr_cents
    FROM monthly_mrr
)
```

The spine is trimmed per customer to their `first_active_month` so that months before signup don't produce false `new` → `reactivation` misclassifications.

#### Observed Distribution (24-month simulation)

| Movement Type | Rows | % |
|---|---|---|
| unchanged | 10,167 | 80.6% |
| new | 1,500 | 11.9% |
| expansion | 531 | 4.2% |
| churned | 351 | 2.8% |
| contraction | 58 | 0.5% |

---

### `analytics.monthly_revenue_overview` (MATERIALIZED VIEW)

One row per month. Aggregates all MRR movement components from `mrr_movement_report`.

#### Key Metrics

**NRR (Net Revenue Retention)**
```
NRR = (beginning_mrr + expansion - contraction - churn) / beginning_mrr × 100
```
Can exceed 100% when expansion outpaces churn. Healthy SaaS target: ≥ 110%.

**GRR (Gross Revenue Retention)**
```
GRR = (beginning_mrr - contraction - churn) / beginning_mrr × 100
```
Always ≤ 100% (no expansion credit). Healthy SaaS target: ≥ 85%.

**Sample — December 2025:**
- MRR: $792,484 | ARR: $9.5M
- Active customers: 1,149
- NRR: 102.52% | GRR: 98.66%
- Monthly churn rate: 2.21%

---

### `analytics.cohort_retention` (MATERIALIZED VIEW)

Monthly cohort retention matrix. One row per `(cohort_month, period_number)`.

**Period 0** = cohort's first active month (always 100%).  
**Period N** = N months after cohort month.

**Sample retention rates (first 6 cohorts):**

| Cohort | Size | M0 | M3 | M6 | M12 |
|---|---|---|---|---|---|
| 2024-01 | 29 | 100% | 93.1% | 86.2% | 69.0% |
| 2024-02 | 34 | 100% | 97.1% | 91.2% | 73.5% |
| 2024-03 | 31 | 100% | 87.1% | 80.6% | 51.6% |
| 2024-04 | 46 | 100% | 84.8% | 73.9% | 65.2% |
| 2024-05 | 44 | 100% | 88.6% | 81.8% | 65.9% |
| 2024-06 | 41 | 100% | 80.5% | 68.3% | 56.1% |

---

### `analytics.customer_health_scores` (MATERIALIZED VIEW)

Composite health score (0–100) for every active customer. Only includes customers with `status = 'active'` on the core product.

#### Component Weights

| Component | Weight | Signal |
|---|---|---|
| `usage_score` | 30% | Recent 3-month session/API activity vs prior 3 months |
| `payment_score` | 25% | Invoice payment rate over last 6 months |
| `support_score` | 20% | Absence of open high/critical severity tickets |
| `tenure_score` | 15% | Months active (5 pts/month, capped at 100) |
| `feature_score` | 10% | Breadth of features used (features_used_count) |

Reference date is anchored to `MAX(month)` in `product_usage` (not `CURRENT_DATE`) so scores remain meaningful when the data's time range doesn't align with the present.

---

### `analytics.churn_risk_segments` (MATERIALIZED VIEW)

Risk tier classification for every active customer, derived from `customer_health_scores`.

#### Risk Tiers

| Tier | Score Range | Recommended Action |
|---|---|---|
| `critical` | < 30 | Immediate CSM escalation |
| `high` | 30–49 | Executive business review this month |
| `medium` | 50–69 | CSM check-in + feature adoption guidance |
| `low` | 70–84 | Quarterly review + expansion opportunity |
| `champion` | ≥ 85 | Upsell / case study / referral candidate |

**Risk flag columns** explain *why* a customer is at risk:
- `flag_usage_declining`
- `flag_payment_issues`
- `flag_support_overloaded`
- `flag_low_feature_adoption`
- `flag_new_customer_risk`

**Distribution (as of latest data):**
| Tier | Customers | MRR |
|---|---|---|
| champion | 97 | $97,467 |
| low | 919 | $639,161 |
| medium | 87 | $33,802 |
| high | 5 | $645 |

---

## Compiling the Analytics Layer

To build and compile the entire analytics layer, use the unified database compiler script. This script automatically handles dependency ordering, drops conflicting stale objects, and provides a row count summary:

```bash
python scripts/build_analytics.py
```

### Manual Compilation Option

If you prefer to run files manually, they must be executed in correct topological order to prevent foreign key or dependency errors:

```bash
# 1. Establish the schema
psql $DATABASE_URL -c "CREATE SCHEMA IF NOT EXISTS analytics;"

# 2. Execute base views
psql $DATABASE_URL -f sql/analytics/01_customer_overview.sql
psql $DATABASE_URL -f sql/analytics/02_subscription_details.sql
psql $DATABASE_URL -f sql/analytics/03_invoice_details.sql

# 3. Execute core MRR models (movement first, then monthly aggregation)
psql $DATABASE_URL -f sql/analytics/05_mrr_movement_report.sql
psql $DATABASE_URL -f sql/analytics/04_monthly_revenue_overview.sql

# 4. Execute cohort retention matrix
psql $DATABASE_URL -f sql/analytics/06_cohort_retention.sql

# 5. Execute health scores and churn segments
psql $DATABASE_URL -f sql/analytics/07_customer_health_scores.sql
psql $DATABASE_URL -f sql/analytics/08_churn_risk_segments.sql
```

---

## Data Quality Validation

To verify the integrity of the analytics layer, run the dedicated validation suite. This executes 23 strict business logic assertions (e.g. verifying that MRR expansion is never negative, NRR remains mathematical, and cohorts sum up to active customer counts):

```bash
# Option A: via Docker
docker exec -i saas-platform-postgres-1 psql -U saas_user -d saas_platform \
  < sql/validation/02_validate_analytics.sql

# Option B: via local psql
psql $DATABASE_URL -f sql/validation/02_validate_analytics.sql
```

All validation assertions should output:
```
All validation checks passed!
```

---

## Refreshing Materialized Views

Since views (`customer_overview`, `subscription_details`, `invoice_details`) query raw tables dynamically, they always reflect the latest database state. 

However, materialized views cache data for maximum performance. If the raw data is regenerated or reloaded, you can refresh them all either by re-running the automated compiler (`python scripts/build_analytics.py`) or by executing the SQL refresh commands:

```sql
REFRESH MATERIALIZED VIEW analytics.mrr_movement_report;
REFRESH MATERIALIZED VIEW analytics.monthly_revenue_overview;
REFRESH MATERIALIZED VIEW analytics.cohort_retention;
REFRESH MATERIALIZED VIEW analytics.customer_health_scores;
REFRESH MATERIALIZED VIEW analytics.churn_risk_segments;
```
