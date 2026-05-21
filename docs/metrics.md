# Metric Definitions — SaaS Revenue & Churn Intelligence Platform

All definitions here are the authoritative source of truth for this project.
Every SQL model must implement these definitions exactly.

---

## Revenue Metrics

### MRR (Monthly Recurring Revenue)

**Definition:** The sum of all monthly-normalized active subscription values at a point in time.

**Formula:**
```
MRR = SUM(mrr_cents) / 100
      WHERE subscription.status = 'active'
      AND snapshot_date BETWEEN subscription.started_at AND COALESCE(subscription.canceled_at, '9999-01-01')
```

**Notes:**
- Annual subscriptions: MRR = annual_value / 12
- Excludes one-time charges, professional services, refunds
- Discounts applied before MRR is recorded on the subscription

---

### ARR (Annual Recurring Revenue)

**Formula:** `ARR = MRR × 12`

---

### ARPA (Average Revenue Per Account)

**Formula:** `ARPA = MRR / COUNT(DISTINCT active_customers)`

---

### Net Revenue Retention (NRR / NDR)

**Definition:** Of the MRR from customers who existed at the start of the period, how much do we have at the end — including expansions but after churn and contractions.

**Formula:**
```
NRR = (Beginning MRR + Expansion MRR - Contraction MRR - Churned MRR) / Beginning MRR
```

**Benchmark:**
- < 100%: losing revenue from existing customers
- 100–110%: healthy
- > 120%: best-in-class (Snowflake, Datadog territory)

---

### Gross Revenue Retention (GRR)

**Definition:** NRR but capped at 100% — expansion excluded.

**Formula:**
```
GRR = (Beginning MRR - Contraction MRR - Churned MRR) / Beginning MRR
```
Capped at 100%.

**Why it matters:** GRR measures your ability to retain existing revenue, ignoring upsells.

---

## MRR Movement Types

This is the heart of the project. Every customer gets exactly one movement type per month.

### Definitions

| Movement Type | Condition |
|---|---|
| **new** | Customer has MRR > 0 this month AND had no MRR in any prior month |
| **reactivation** | Customer has MRR > 0 this month AND had MRR = 0 last month AND had MRR > 0 in some prior month |
| **expansion** | Customer has MRR > 0 this month AND MRR > prior month MRR AND was active last month |
| **contraction** | Customer has MRR > 0 this month AND MRR < prior month MRR AND was active last month |
| **churned** | Customer has MRR = 0 this month AND had MRR > 0 last month |
| **unchanged** | Customer has MRR > 0 this month AND MRR = prior month MRR |

**Important edge cases:**
- A customer upgrading and downgrading in the same month: net change determines the movement type
- Trial conversions: movement type = new on first paying month
- Paused subscriptions: treated as MRR = 0 (contributes to churn if paused from active)

### MRR Movement SQL Pattern (interview-ready)

```sql
WITH monthly_mrr AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', snapshot_date) AS month,
        SUM(mrr_cents) AS mrr_cents
    FROM subscription_snapshots
    GROUP BY 1, 2
),
mrr_with_lag AS (
    SELECT
        customer_id,
        month,
        mrr_cents,
        LAG(mrr_cents) OVER (PARTITION BY customer_id ORDER BY month) AS prev_mrr_cents,
        MIN(month) OVER (PARTITION BY customer_id) AS first_active_month
    FROM monthly_mrr
),
movement AS (
    SELECT
        customer_id,
        month,
        mrr_cents,
        prev_mrr_cents,
        CASE
            WHEN prev_mrr_cents IS NULL AND mrr_cents > 0                          THEN 'new'
            WHEN prev_mrr_cents = 0    AND mrr_cents > 0
                 AND first_active_month < month                                    THEN 'reactivation'
            WHEN prev_mrr_cents > 0    AND mrr_cents = 0                           THEN 'churned'
            WHEN prev_mrr_cents > 0    AND mrr_cents > prev_mrr_cents              THEN 'expansion'
            WHEN prev_mrr_cents > 0    AND mrr_cents < prev_mrr_cents              THEN 'contraction'
            WHEN prev_mrr_cents > 0    AND mrr_cents = prev_mrr_cents              THEN 'unchanged'
        END AS movement_type,
        mrr_cents - COALESCE(prev_mrr_cents, 0) AS mrr_change_cents
    FROM mrr_with_lag
)
SELECT * FROM movement;
```

---

## Churn Metrics

### Customer Churn Rate (Logo Churn)

**Formula:**
```
Customer Churn Rate = Churned Customers in Period / Customers at Start of Period
```

**Monthly vs. Annual:** Report both. Monthly churn of 2% = ~22% annual churn.

### Revenue Churn Rate (MRR Churn)

**Formula:**
```
Revenue Churn Rate = Churned MRR in Period / MRR at Start of Period
```

---

## Cohort Metrics

### Cohort Retention Rate

**Definition:** Of all customers who subscribed in month M, what % are still active at month M+N?

**Formula:**
```
Retention(cohort_month, N) = 
    Active customers from cohort at month M+N 
    / Total customers in cohort at month M
```

**Output format:** Triangle retention matrix (cohort rows × months columns)

---

## Customer Health Score

Composite score (0–100) per customer. Higher = healthier.

| Signal | Weight | Direction |
|---|---|---|
| Product usage trend (3-month) | 30% | Declining = bad |
| Feature adoption breadth | 20% | More features = better |
| Payment history | 20% | Failed payments = bad |
| Support ticket volume & severity | 15% | High severity = bad |
| Tenure | 10% | Longer = better |
| Plan tier | 5% | Enterprise = better |

**Risk buckets:**
- 80–100: Healthy
- 60–79: Neutral
- 40–59: At Risk
- 0–39: Critical

---

## Customer Lifetime Value (LTV)

**Formula:**
```
LTV = ARPA / Monthly Churn Rate
```

**Segmented LTV:** Calculate per segment (SMB, mid-market, enterprise) since churn rates differ dramatically.

---

## Key SaaS Benchmarks (for interview context)

| Metric | Good | Great | Best-in-class |
|---|---|---|---|
| Monthly MRR Churn | < 2% | < 1% | < 0.5% |
| NRR | > 100% | > 110% | > 130% |
| GRR | > 80% | > 90% | > 95% |
| SMB Monthly Churn | 3–7% typical | | |
| Enterprise Monthly Churn | 0.5–1.5% typical | | |
