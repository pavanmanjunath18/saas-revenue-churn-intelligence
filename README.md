# SaaS Revenue & Churn Intelligence Platform

**A subscription analytics platform that transforms raw billing events into decision-ready revenue intelligence.**

Built to answer the questions every B2B SaaS company needs answered: How is MRR growing? Where is revenue being lost? Which customers are at risk of churning?

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B?logo=streamlit)](https://saas-revenue-churn-intelligence.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Dashboard Preview

| Home | Revenue Overview | MRR Waterfall |
|------|-----------------|---------------|
| ![Home](docs/assets/01_home.png) | ![Revenue](docs/assets/02_revenue_overview.png) | ![Waterfall](docs/assets/03_mrr_waterfall.png) |

| Churn Analysis | Cohort Retention | Customer Health |
|----------------|-----------------|----------------|
| ![Churn](docs/assets/04_churn_analysis.png) | ![Cohort](docs/assets/05_cohort_retention.png) | ![Health](docs/assets/06_customer_health.png) |

---

## The Problem This Solves

Raw billing data from SaaS payment systems is event-sourced and non-continuous. Individual invoice records, payment logs, and subscription state changes don't naturally answer business questions like:

- *What is our exact MRR this month, and how much came from new customers vs. upsells?*
- *What is our Net Revenue Retention — are we growing revenue from existing customers or losing it?*
- *Which customers are showing early warning signals that they'll churn next month?*

Answering these requires an **analytics layer** that translates discrete billing events into point-in-time subscription metrics. That translation is what this platform builds.

---

## Key Metrics (from the live dataset)

| Metric | Value | Context |
|--------|-------|---------|
| Peak MRR | **$792,484** | Dec 2025, grown from $0 at Jan 2024 launch |
| ARR | **$9.5M** | 24-month run rate |
| Active Customers | **1,149** | Across SMB, mid-market, enterprise |
| Net Revenue Retention | **102.2% avg** | Expansion outpaces churn consistently |
| Gross Revenue Retention | **97.6% avg** | Strong base retention before upsell |
| Avg Monthly Churn Rate | **2.58%** | 351 churn events over 24 months |
| M3 Cohort Retention | **90.2%** | Strong early-stage stickiness |
| M12 Cohort Retention | **65.2%** | Meaningful long-tail decay |
| Avg Health Score | **76.8 / 100** | Weighted composite across 1,108 active accounts |

---

## What's Inside

- **Synthetic data generator** — 1,500 B2B customers with correlated billing behavior across SMB, mid-market, and enterprise segments. Cancellations follow payment failures. Enterprise accounts churn less than SMB. Usage correlates with subscription tier.
- **Relational data warehouse** — 12 normalized PostgreSQL tables with 50K+ rows covering the full subscription billing domain: products, plans, customers, subscriptions, invoices, payments, refunds, usage, and support tickets.
- **Analytics SQL layer** — 8 models (3 views + 5 materialized views) that implement industry-standard SaaS metrics: MRR movement waterfall, NRR/GRR, cohort retention matrix, and weighted customer health scores.
- **MRR state machine** — the core model classifies every customer-month into one of six mutually exclusive movement types using PostgreSQL window functions, producing a complete subscription ledger.
- **Interactive dashboard** — 5-page Streamlit application with 20+ Plotly charts, date range filters, drill-down selectors, and a per-account radar chart.
- **23 data quality assertions** — automated validation suite confirming model correctness before every analysis.

---

## Architecture

```mermaid
flowchart LR
    A[("Python\nSimulator\nFaker · NumPy")]
    B[/"12 CSV files\n50K+ rows"/]
    C[("PostgreSQL\nraw schema\n12 tables")]
    D[("PostgreSQL\nanalytics schema\n8 models")]
    E["Streamlit\nDashboard\n5 pages · Plotly"]

    A -->|generate_mock_data.py| B
    B -->|load_data.py| C
    C -->|SQL window functions\nCTEs · materialized views| D
    D -->|SQLAlchemy\nst.cache_data| E
```

**Deployment:**
```
Local dev:   Docker Compose PostgreSQL  →  Streamlit localhost:8501
Production:  Neon PostgreSQL (cloud)    →  Streamlit Community Cloud
```

---

## Data Pipeline

```mermaid
flowchart TD
    subgraph "1 · Data Generation"
        G1["generate_mock_data.py\n1,500 customers\n24-month simulation"]
    end

    subgraph "2 · Raw Schema (PostgreSQL)"
        R1["products · plans"]
        R2["customers · discounts"]
        R3["subscriptions · subscription_items"]
        R4["invoices · invoice_line_items · payments · refunds"]
        R5["product_usage · support_tickets"]
    end

    subgraph "3 · Analytics Schema"
        direction TB
        A1["customer_overview (VIEW)"]
        A2["subscription_details (VIEW)"]
        A3["invoice_details (VIEW)"]
        A4["mrr_movement_report ⭐\n(MATERIALIZED VIEW)\nCore model"]
        A5["monthly_revenue_overview\n(MATERIALIZED VIEW)"]
        A6["cohort_retention\n(MATERIALIZED VIEW)"]
        A7["customer_health_scores\n(MATERIALIZED VIEW)"]
        A8["churn_risk_segments\n(MATERIALIZED VIEW)"]

        A4 --> A5
        A7 --> A8
    end

    subgraph "4 · Dashboard"
        D1["Revenue Overview"]
        D2["MRR Waterfall"]
        D3["Churn Analysis"]
        D4["Cohort Retention"]
        D5["Customer Health"]
    end

    G1 --> R1 & R2 & R3 & R4 & R5
    R1 & R2 & R3 & R4 & R5 --> A1 & A2 & A3 & A4 & A6
    A4 --> D1 & D2 & D3
    A6 --> D4
    A8 --> D5
```

---

## Database Schema

12 normalized tables in the `raw` schema organized around the subscription billing domain:

```
raw.products          ← Product catalog (2 core products)
raw.plans             ← Pricing tiers (10 plans: Starter → Enterprise)
raw.customers         ← 1,500 B2B accounts (SMB / mid-market / enterprise)
raw.discounts         ← Promotional discounts applied to subscriptions
raw.subscriptions     ← 2,394 subscription lifecycle records
raw.subscription_items← Add-on line items on subscriptions
raw.invoices          ← 10,495 monthly billing documents
raw.invoice_line_items← Line-item detail per invoice
raw.payments          ← 9,120 payment attempt records
raw.refunds           ← 157 refund transactions
raw.product_usage     ← 12,256 monthly usage telemetry rows
raw.support_tickets   ← 2,908 customer support interactions
```

**Referential integrity** is enforced with explicit primary keys, foreign keys, CHECK constraints on categoricals, and indexes on all filter/join columns.

---

## Analytics Models

| Model | Type | Rows | Purpose |
|-------|------|------|---------|
| `customer_overview` | VIEW | 1,500 | Customer profile + current subscription state |
| `subscription_details` | VIEW | 2,394 | Subscription enriched with movement type |
| `invoice_details` | VIEW | 10,495 | Invoice + payment status enriched |
| `mrr_movement_report` ⭐ | MATVIEW | 12,607 | **Core model** — monthly MRR state machine |
| `monthly_revenue_overview` | MATVIEW | 24 | Company-wide MRR, ARR, NRR, GRR, ARPA |
| `cohort_retention` | MATVIEW | 300 | Cohort triangle — 24 cohorts × 12 periods |
| `customer_health_scores` | MATVIEW | 1,108 | Composite health score per active account |
| `churn_risk_segments` | MATVIEW | 1,108 | Risk tier + recommended actions |

### The MRR State Machine

The `mrr_movement_report` is the most technically sophisticated model. For each customer-month, it:

1. Builds a customer-specific date spine (avoiding false reactivation from month-0 records)
2. Uses `LAG()` window functions to compare current vs. prior period MRR
3. Classifies each row into one of six mutually exclusive movement types:

| Movement Type | Definition | % of Rows |
|---|---|---|
| `unchanged` | Active, same MRR as prior month | 80.6% |
| `new` | First month active | 11.9% |
| `expansion` | MRR increased from prior month | 4.2% |
| `churned` | Active last month, $0 this month | 2.8% |
| `contraction` | MRR decreased (but still > $0) | 0.5% |
| `reactivation` | Was $0, now active again | < 0.1% |

### Health Score Weighting

| Signal | Weight | Source |
|--------|--------|--------|
| Usage trend (sessions, API calls, features) | 30% | `product_usage` |
| Payment health (failure rate, outstanding) | 25% | `payments`, `invoices` |
| Support load (ticket volume, severity) | 20% | `support_tickets` |
| Account tenure | 15% | `subscriptions` |
| Feature adoption breadth | 10% | `product_usage` |

---

## Core SaaS Metrics Implemented

| Metric | Formula | Implementation |
|--------|---------|----------------|
| **MRR** | Sum of monthly-normalized active subscription values | `mrr_movement_report` → `monthly_revenue_overview` |
| **ARR** | MRR × 12 | `monthly_revenue_overview` |
| **Net Revenue Retention (NRR)** | (Beginning MRR + Expansion − Contraction − Churn) / Beginning MRR | `monthly_revenue_overview` |
| **Gross Revenue Retention (GRR)** | NRR capped at 100% (no expansion credit) | `monthly_revenue_overview` |
| **ARPA** | MRR / Active customers | `monthly_revenue_overview` |
| **Customer Churn Rate** | Churned customers / Prior month active customers | `monthly_revenue_overview` |
| **Cohort Retention %** | Active customers in cohort at period N / Cohort size | `cohort_retention` |
| **Health Score** | Weighted composite 0–100 across 5 signals | `customer_health_scores` |

---

## Dashboard Pages

### Home — Executive Summary
Top-level KPIs with month-over-month deltas. Navigation to all five analysis pages. Risk alert when high/critical tier accounts exist.

### Revenue Overview
24-month MRR/ARR trajectory, NRR vs. GRR trend lines, revenue by segment (SMB/mid-market/enterprise stacked bars), ARPA trend, and monthly churn rate.

### MRR Waterfall
Interactive date-range waterfall decomposing monthly MRR movement into new, expansion, reactivation, contraction, and churned components. Customer count movement chart. Full monthly detail table.

### Churn Analysis
Monthly churn rate trend, churned MRR bar chart, segment-level churn breakdown, industry concentration (top 10), segment donut, and largest churned accounts table.

### Cohort Retention
Interactive retention triangle heatmap (24 cohorts × up to 12 periods), average retention curve, cohort size bars, and single-period snapshot comparison across all cohorts.

### Customer Health
Health score distribution histogram, risk tier MRR donut, health vs. MRR scatter (each dot = one account), per-account radar chart comparing 5 score components to average, and at-risk accounts table with recommended actions.

---

## Validation

The `sql/validation/02_validate_analytics.sql` file contains **23 data quality assertions** run after every build:

- Period-0 cohort retention = 100% for all cohorts
- Health scores bounded [0, 100]
- GRR never exceeds 100%
- MRR movement types are mutually exclusive and exhaustive
- No negative MRR values
- All active customers have a health score
- NRR formula cross-validates against movement components

All 23 assertions pass on the current dataset.

---

## Sample Insights

These findings emerge from the 24-month synthetic dataset:

- **NRR averaged 102.2%** across the full period — expansion revenue from upsells consistently outpaced churn, meaning the business grows revenue from its existing customer base without relying solely on new acquisition.
- **Enterprise segment retains at 86.5% at month 12** vs. **SMB at 58.3%** — a 28-percentage-point gap that validates focusing customer success resources on larger accounts.
- **Churn accelerated in mid-2025** — the monthly churn rate spiked above 4% in Jul 2024 before stabilizing at ~2.5%, suggesting an early product-market fit issue that resolved itself by late 2024.
- **Payment failure is the strongest churn predictor** — accounts in the `critical` risk tier have 3× the invoice failure rate of `champion` tier accounts.
- **M3 retention of 90.2% signals strong product stickiness** — customers who survive the first 90 days are significantly more likely to remain long-term.

---

## Setup Instructions

### Option A: Local development (Docker)

**Prerequisites:** Docker Desktop, Python 3.10+

```bash
# 1. Clone the repository
git clone https://github.com/pavanmanjunath18/saas-revenue-churn-intelligence.git
cd saas-revenue-churn-intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Start PostgreSQL
docker compose up -d
# Wait for: Status = healthy

# 5. Generate synthetic data
python scripts/generate_mock_data.py

# 6. Create schema and load data
psql postgresql://saas_user:saas_pass@localhost:5433/saas_platform \
  -f sql/schema/01_create_schema.sql
python scripts/load_data.py

# 7. Build analytics models
psql postgresql://saas_user:saas_pass@localhost:5433/saas_platform \
  -f sql/analytics/99_run_all_analytics.sql

# 8. Run the dashboard
streamlit run dashboards/streamlit_app.py
# Opens at http://localhost:8501
```

### Option B: Cloud database (Neon / Supabase)

```bash
# 1. Get a free PostgreSQL URL from neon.tech
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# 2. One-command setup (generates data, loads tables, builds models)
bash scripts/setup_cloud_db.sh
```

Then set `DATABASE_URL` in your Streamlit Cloud app secrets.

---

## Deployment (Streamlit Cloud)

1. Fork this repository
2. Create a free PostgreSQL database at [neon.tech](https://neon.tech)
3. Run `bash scripts/setup_cloud_db.sh` with your Neon URL
4. Deploy to [share.streamlit.io](https://share.streamlit.io):
   - **Repository:** `your-username/saas-revenue-churn-intelligence`
   - **Main file path:** `dashboards/streamlit_app.py`
5. Add your database URL under **Settings → Secrets**:
   ```toml
   DATABASE_URL = "postgresql://..."
   ```

---

## Project Structure

```
saas-revenue-churn-intelligence/
│
├── dashboards/                   # Streamlit application
│   ├── pages/
│   │   ├── 01_Revenue_Overview.py
│   │   ├── 02_MRR_Waterfall.py
│   │   ├── 03_Churn_Analysis.py
│   │   ├── 04_Cohort_Retention.py
│   │   └── 05_Customer_Health.py
│   ├── streamlit_app.py          # Home page / entry point
│   ├── db.py                     # Connection chain (secrets → .env → default)
│   └── style.py                  # Color tokens + Plotly layout factory
│
├── sql/
│   ├── schema/
│   │   └── 01_create_schema.sql  # 12-table DDL with PK/FK/indexes
│   ├── analytics/
│   │   ├── 01–08_*.sql           # Individual model definitions
│   │   └── 99_run_all_analytics.sql  # Full build in dependency order
│   └── validation/
│       └── 02_validate_analytics.sql  # 23 data quality assertions
│
├── scripts/
│   ├── generate_mock_data.py     # Synthetic data generator
│   ├── load_data.py              # Type-safe CSV → PostgreSQL loader
│   ├── validate_generated_data.py
│   └── setup_cloud_db.sh         # One-command cloud DB bootstrap
│
├── data/synthetic/               # Generated CSVs (gitignored)
├── docs/                         # Technical documentation
│   ├── assets/                   # Screenshots and diagrams
│   ├── analytics_layer.md        # SQL model reference
│   ├── metrics.md                # SaaS metric definitions
│   ├── database_setup.md         # Detailed setup guide
│   ├── insights_report.md        # Sample analyst deliverable
│   ├── project_audit.md          # Internal quality review
│   └── v2_improvement_plan.md    # Roadmap
│
├── tests/
│   └── test_data_quality.py      # Pytest data quality checks
│
├── .github/workflows/ci.yml      # GitHub Actions CI
├── .streamlit/config.toml        # Streamlit configuration
├── docker-compose.yml            # Local PostgreSQL container
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment template
```

---

## Project Status

| Component | Status |
|-----------|--------|
| Synthetic data generator | ✅ Complete |
| PostgreSQL schema (raw) | ✅ Complete |
| Analytics SQL layer (8 models) | ✅ Complete |
| Data validation (23 assertions) | ✅ Complete |
| Streamlit dashboard (5 pages) | ✅ Complete |
| Docker local setup | ✅ Complete |
| Cloud deployment (Streamlit + Neon) | ✅ Live |
| GitHub Actions CI | ✅ Active |
| Documentation | ✅ Complete |
| Segment-level NRR/GRR | 🔜 Future |
| dbt conversion | 🔜 Future |
| Predictive churn model (ML) | 🔜 Future |

---

## Future Improvements

- **dbt conversion** — Migrate SQL models to dbt format with `ref()` dependencies, `schema.yml` tests, and auto-generated lineage documentation
- **Segment-level retention** — Break out NRR/GRR by SMB/mid-market/enterprise to surface the enterprise retention premium explicitly
- **Predictive churn model** — Add a scikit-learn model (logistic regression or gradient boosting) trained on health score features to output a 30-day churn probability
- **Alerting simulation** — Script that identifies accounts crossing risk tier thresholds and simulates a customer success team notification
- **Historical health snapshots** — Daily health score snapshots to enable trend analysis ("health dropped 15 points this month")
- **Makefile** — `make setup`, `make refresh`, `make test` interface for the full workflow

---

## Resume Bullets

### For Analytics Engineer / Data Engineer roles
- Engineered a PostgreSQL analytics layer modeling subscription revenue for 1,500 B2B SaaS accounts — implemented MRR movement classification (new/expansion/contraction/churn/reactivation) using SQL window functions and customer-specific date spine logic to compute industry-standard NRR (102.2%) and GRR (97.6%)
- Built a topologically ordered SQL build pipeline (8 models, 3 VIEWs + 5 MATERIALIZED VIEWs) transforming 50K+ raw billing events into decision-ready metrics; validated with 23 automated data quality assertions
- Deployed a full analytics stack (PostgreSQL on Neon + Streamlit Cloud) with environment-agnostic connection management supporting local Docker, .env, and Streamlit secrets configuration

### For Data Analyst roles
- Designed and deployed a 5-page interactive analytics dashboard (Streamlit + Plotly) surfacing MRR growth, churn patterns, cohort retention triangles, and customer health risk scores for 1,100+ active accounts
- Developed a composite customer health scoring model (0–100) weighted across 5 behavioral signals — usage trends, payment history, support load, tenure, and feature adoption — to proactively identify at-risk accounts
- Produced quantitative insights from 24-month B2B SaaS simulation: identified 28pp retention gap between enterprise and SMB cohorts at month 12, and correlated payment failure rate with churn probability

### For Data Scientist roles
- Built a weighted multi-factor scoring system for B2B SaaS customer health, combining usage telemetry, payment behavior, and support signal features into a continuous 0–100 risk score with validated tier separation
- Implemented cohort retention analysis across 24 monthly cohorts tracking customer survival curves from month 0 through month 12, revealing M3 retention of 90.2% and M12 retention of 65.2%
- Designed a synthetic behavioral data generator with correlated variables — cancellation probability, usage level, and support ticket frequency are co-determined by segment and payment history, producing statistically realistic churn patterns

---

## Interview Talking Points

**30-second version:**
> "I built an end-to-end subscription analytics platform that solves a real problem in SaaS: raw billing data is event-sourced and you can't answer basic revenue questions directly from it. I built a PostgreSQL analytics layer that classifies every customer-month into a movement type — new, expansion, contraction, or churn — and uses that to compute NRR, cohort retention, and customer health scores. It's deployed live on Streamlit Cloud."

**2-minute technical version:**
> "The core technical challenge is what I'd call the subscription ledger problem. Stripe gives you invoice events. But to compute MRR, you need point-in-time snapshots. To compute NRR, you need to compare two consecutive monthly snapshots per customer and classify the delta. My `mrr_movement_report` model solves this using a customer-specific date spine — not a global one, because that causes false reactivation events — and LAG window functions to compare adjacent months. Each row gets classified into one of six mutually exclusive movement types. Everything else — monthly revenue overview, NRR, GRR — derives from that one model.
>
> For customer health, I built a weighted composite score across five independently sourced signals: usage from the product telemetry table, payment health from invoices and payment attempts, support load from ticket volume and priority, tenure from subscription start date, and feature breadth from distinct features used per month. The weights (30/25/20/15/10) are defensible but also configurable — that's a design choice I'd articulate in an interview.
>
> The whole thing is deployed on Streamlit Cloud connected to Neon PostgreSQL, with a GitHub Actions CI pipeline that runs syntax checks and data generation on every push."

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Data: Realistic synthetic B2B SaaS simulation — not real company data. The dataset reflects statistically plausible subscription billing patterns but does not represent any actual business.*
