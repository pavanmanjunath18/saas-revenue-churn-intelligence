# Interview Notes — SaaS Revenue & Churn Intelligence Platform

This document is your cheat sheet. Study it before every interview.
Every decision in this project has a defensible answer.

---

## How to introduce this project

> "I built a SaaS revenue and churn analytics platform from scratch — including synthetic data generation that mimics Stripe-style billing behavior, a full PostgreSQL analytics layer with MRR movement analysis, cohort retention, and customer health scoring. The core challenge was getting the MRR movement logic right — it's more subtle than it looks."

**What this signals:**
- You understand SaaS business metrics (not just SQL)
- You can build end-to-end data systems
- You think about data modeling, not just queries
- You know what interviewers care about

---

## Questions you will get asked

### "Walk me through your MRR movement logic."

**Answer:**
"For every customer and every month, I compare their current MRR to the prior month's MRR using a LAG window function partitioned by customer. The movement types are mutually exclusive:

- **New**: first month they have MRR > 0, no prior history
- **Reactivation**: MRR > 0 this month, was 0 last month, but had MRR previously
- **Expansion**: MRR increased vs. last month, still active
- **Contraction**: MRR decreased vs. last month, still active
- **Churned**: MRR went to 0 from > 0
- **Unchanged**: same MRR as last month

The tricky case is reactivation vs. new — both have no prior-month MRR in the lag, but reactivation requires checking whether the customer ever had MRR before. I handle this with `MIN(month) OVER (PARTITION BY customer_id)` to detect first-ever active month."

---

### "What's the difference between NRR and GRR?"

**Answer:**
"NRR (Net Revenue Retention) measures the total revenue you retain from existing customers after accounting for expansion, contraction, and churn. It can exceed 100% if expansion outweighs churn.

GRR (Gross Revenue Retention) is capped at 100% — it measures only your ability to retain revenue without upsell, so expansion doesn't count. A company can have NRR of 120% but GRR of 85%, which tells you they're good at upselling but losing meaningful revenue to churn and downgrades."

---

### "Why did you use PostgreSQL instead of a cloud warehouse?"

**Answer:**
"For local development and a portfolio project, PostgreSQL is the right choice — it supports everything I needed: window functions, CTEs, lateral joins, materialized views. The SQL I wrote is also compatible with BigQuery and Snowflake with minimal changes (mostly date function syntax). In a real company I'd run this on a warehouse, but the analytics logic is the same."

---

### "How did you model churn in your data?"

**Answer:**
"I defined churn at the subscription level — a customer churns in the month their last active subscription is canceled and not renewed. For MRR churn rate, it's churned MRR divided by beginning MRR for the period.

In the synthetic data, I also modeled leading indicators of churn — declining product usage in the 2–4 months before cancellation, increasing support ticket severity, and payment failures. This lets me build a churn risk model that's actually predictive, not just descriptive."

---

### "What's a cohort retention table and how did you build it?"

**Answer:**
"A cohort retention table shows, for each group of customers who started in the same month, what percentage are still active at months 1, 2, 3... through month N.

I built it by: first assigning each customer a cohort month (first subscription start month), then for each subsequent month calculating whether they still had active MRR. The result is a triangle matrix — month 0 is always 100%, and each column shows the retention percentage at that month offset."

---

### "What would you add to this if you had more time?"

**Answer (choose 2–3):**
- "A predictive churn model using scikit-learn, with SHAP values to explain which signals matter most — declining usage, payment failures, or support volume."
- "dbt integration to replace my raw SQL files with proper models, tests, and documentation."
- "A REST API using FastAPI so this data could be consumed by downstream systems, not just dashboards."
- "Streaming ingestion simulation using Kafka to replace the batch CSV loader."

---

## Business context you should know

**Why MRR matters more than revenue:**
One-time revenue is lumpy and hard to forecast. MRR is the steady-state signal of business health. Investors and operators care about MRR because it's predictable and compounding.

**Why NRR > 100% is a superpower:**
If NRR > 100%, you grow revenue from existing customers even with zero new sales. This is why Snowflake and Datadog can have high churn in customer count but still grow revenue — their expansion from remaining customers more than offsets losses.

**Why SMB churn is structurally higher:**
SMB companies have less budget stability, more volatility, and less organizational momentum. They cancel subscriptions when cash is tight. Enterprise customers have longer procurement cycles and switching costs — once you're embedded, it's hard to cancel.

**Why cohort analysis is better than aggregate churn rate:**
Aggregate churn rate is a single number that hides composition effects. If you're acquiring more SMB customers (higher churn) your aggregate churn rate rises even if each segment is stable. Cohort analysis reveals whether behavior is actually changing or just the customer mix.

---

## Red flags to avoid in interviews

- Don't say "I built this to learn SQL" — say "I built this to understand how SaaS revenue analytics works operationally"
- Don't say "the data is fake" — say "I generated realistic synthetic data with behavioral patterns that mimic actual SaaS billing behavior"
- Don't claim expertise you don't have — if asked about something outside this project, say "that's something I'd be excited to learn — here's how I'd approach it"
- Don't confuse MRR churn with customer churn — they're related but different metrics
