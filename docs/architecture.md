# Architecture — SaaS Revenue & Churn Intelligence Platform

## System Overview

This platform simulates the analytics infrastructure of a B2B SaaS company. It ingests synthetic billing and usage data, models it through a SQL analytics layer, and surfaces revenue and churn intelligence through dashboards.

The architecture mirrors how a real analytics engineering team would build this at a Series A/B SaaS company.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    DATA GENERATION                       │
│   Python synthetic data generator (Stripe-style)         │
│   12 tables · 500 customers · 24 months                  │
└─────────────────────────┬───────────────────────────────┘
                          │ CSV → PostgreSQL
┌─────────────────────────▼───────────────────────────────┐
│                    RAW DATA LAYER                         │
│   PostgreSQL 15                                           │
│   Schema: raw                                             │
│   Tables: customers, subscriptions, invoices,             │
│           payments, usage, support_tickets, ...           │
└─────────────────────────┬───────────────────────────────┘
                          │ SQL models (dbt-style)
┌─────────────────────────▼───────────────────────────────┐
│                  ANALYTICS LAYER                          │
│   Schema: analytics                                       │
│   Models: customer_overview, mrr_movement_report,         │
│           cohort_retention, churn_risk, health_scores     │
└─────────────────────────┬───────────────────────────────┘
                          │ Tableau / Power BI
┌─────────────────────────▼───────────────────────────────┐
│                  DASHBOARD LAYER                          │
│   Revenue Overview · Churn Analysis · Cohort Retention    │
│   Customer Health · MRR Waterfall                         │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Choices

| Layer | Tool | Why |
|---|---|---|
| Data Generation | Python (Faker, NumPy, Pandas) | Full control over realistic behavioral patterns |
| Database | PostgreSQL 15 | Industry standard for analytics; window functions, CTEs |
| Analytics SQL | Plain SQL (dbt-inspired structure) | Readable, defensible, interview-friendly |
| Containerization | Docker Compose | Reproducible local environment |
| Dashboards | Streamlit (Python) | High-performance interactive dashboarding connected directly to DB |
| CI/CD | GitHub Actions | Automated schema validation and data quality checks |

---

## Data Flow

1. `scripts/generate_mock_data.py` — generates 12 CSV files into `data/synthetic/`
2. `scripts/load_data.py` — loads CSVs into PostgreSQL `raw` schema
3. `sql/schema/` — DDL for all raw tables
4. `sql/analytics/` — SQL analytics models compiled in topological order
5. `sql/validation/` — data quality and business logic assertions
6. `dashboards/` — interactive Streamlit app rendering revenue and churn analytics


---

## Schema Design Principles

- All tables have surrogate UUID primary keys
- All timestamps in UTC
- Soft deletes where applicable (is_deleted flag)
- Subscription MRR always stored as monthly-normalized value
- Annual subscriptions: MRR = total_value / 12
- All monetary values in cents (integer) to avoid floating point issues

---

## Key Architectural Decisions

See `decisions.md` for full reasoning. Summary:

1. Store MRR as monthly-normalized value at subscription level — avoids recalculation complexity
2. Separate `subscription_items` from `subscriptions` — supports multi-product + add-ons
3. Model MRR movement as a point-in-time snapshot per customer per month — not event-sourced
4. Health score computed in SQL, not Python — keeps analytics close to data
5. Cohort defined by first subscription start month, not signup date

---

## Environments

| Environment | Database | Notes |
|---|---|---|
| Local dev | Docker PostgreSQL | `docker compose up` |
| Test | In-memory SQLite (future) | Schema validation only |
| Demo | Hosted PostgreSQL (Phase 5) | For recruiters to query live |
