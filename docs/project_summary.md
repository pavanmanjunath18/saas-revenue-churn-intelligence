# B2B SaaS Revenue & Churn Intelligence Platform

## Executive Project Summary

This project showcases a production-ready **B2B SaaS Revenue and Churn Intelligence Platform**. It is designed to model and solve the exact analytical and data engineering challenges that SaaS companies face when scaling their commercial operations: **understanding recurring revenue movement, cohort retention lifecycles, and customer risk segments.**

By constructing a robust data pipeline consisting of a custom Python behavioral simulator, a highly structured PostgreSQL relational database, and an analytics engine, this platform delivers enterprise-grade intelligence to business leaders via a beautiful, interactive Streamlit application.

---

## The Core Challenge: SaaS Analytics Complexity

Most early-stage SaaS companies struggle to answer basic business questions because raw billing tables from providers like Stripe or Recurly are event-driven, noisy, and complex. Answering:
1. *What was our exact MRR at the end of last month?*
2. *How much did our existing customers expand or contract?*
3. *What is our Net Revenue Retention (NRR) and Gross Revenue Retention (GRR)?*

requires an analytics layer that can translate individual invoice events, payment logs, and usage records into continuous, point-in-time subscription metrics. 

This project implements that analytical transition.

---

## Technical Architecture & Methodology

```
                                  [ PYTHON SIMULATOR ]
                      Generates realistic, correlated data (Faker/NumPy)
                                           │
                                           ▼
                                   [ CSV SEED DATA ]
                          12 Raw billing and usage CSV files
                                           │
                                           ▼
                                [ POSTGRESQL RAW LAYER ]
                       12 Structured Tables with strict PK/FK DDL
                                           │
                                           ▼
                           [ POSTGRESQL ANALYTICS MODELING ]
                   8 Core views/materialized views built with CTEs & Lag
                                           │
                                           ▼
                                 [ STREAMLIT INTERFACE ]
                    5-Page Dashboard with interactive Plotly visuals
```

### 1. Data Ingestion & Integrity
* **Raw Schema:** Spans 12 normalized tables (`products`, `plans`, `customers`, `discounts`, `subscriptions`, `subscription_items`, `invoices`, `invoice_line_items`, `payments`, `refunds`, `product_usage`, and `support_tickets`) containing **50,000+ records**.
* **Integrity Assertions:** Enforced by explicit primary and foreign keys, custom enum checkers, and strict constraints (e.g., `canceled_at > started_at`).
* **Validation Suite:** A standalone suite of 21 integrity and sanity queries executing automatically to ensure absolute data consistency before modeling.

### 2. The SQL Analytics Engine
At the core of the database is the **Analytics Layer**, compiling 8 SQL models sequentially to compute key recurring business metrics:
* **`subscription_details` & `customer_overview`:** Abstract base queries calculating total subscriptions, lifecycles, and customer segmentation demographics.
* **`mrr_movement_report`:** A monthly state machine that classifies every customer-month into one of six mutually exclusive categories: **new**, **reactivation**, **expansion**, **contraction**, **churned**, or **unchanged**. It leverages PostgreSQL SQL window functions (`LAG` and partition-by statements) to analyze month-over-month shifts.
* **`monthly_revenue_overview`:** Computes company-wide aggregate MRR, ARR, NRR, GRR, ARPA, and logo counts by month.
* **`cohort_retention`:** Generates a dynamic cohort matrix, grouping customers by their initial subscription signup month and tracking their monthly logo and revenue decay over a 24-month horizon.
* **`customer_health_scores` & `churn_risk_segments`:** Employs weighted composite scoring (usage trends, ticket severity, payment failures, plan tier, and annual commitment bonuses) to bucket active accounts into risk categories (`Healthy`, `Neutral`, `At Risk`, `Critical`).

### 3. Streamlit Analytics Front-End
Surfaces all modeled data via an elite web application:
* Highly responsive grid-based KPI cards.
* Interactive subplots charting MRR alongside active customer levels.
* Stacked bars illustrating segment-level contributions.
* Dynamic date-slider waterfalls separating revenue gains and losses.
* Full-matrix heatmaps visualizing customer retention.
* Actionable CS checklists detailing at-risk accounts for immediate playbooks.

---

## Key Analytical Insights

Using the simulated B2B SaaS dataset, the analytics layer reveals real-world SaaS operational patterns:
* **Strong Net Retention (NRR):** Company NRR averages **103%**, demonstrating that expansion of the existing customer base outpaces churn.
* **Segment Divergence:** SMB cohorts experience rapid logo decay (churning at ~60% over 24 months), whereas Enterprise cohorts remain remarkably flat (13.8% total churn over 2 years), validating an enterprise-focused sales strategy.
* **Leading Indicators:** Health scores successfully anticipate customer actions. Retained customers exhibit **11.3** average feature interactions compared to **10.2** for churned accounts, and payment failures are 21% higher among churned accounts.
