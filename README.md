# SaaS Revenue & Churn Intelligence Platform

An enterprise-grade B2B SaaS analytics engineering and intelligence platform. It simulates real-world commercial operations, models transactional billing events through a topological SQL analytics schema, and translates raw events into point-in-time subscription health metrics.

---

## 🌟 Executive Project Overview

Early-stage B2B SaaS companies frequently struggle with data-driven decision-making because raw billing records (from providers like Stripe or Recurly) are event-sourced, unstructured, and highly volatile. Simple business questions like—*What is our exact MRR today?*, *What is our Net Revenue Retention (NRR) rate?*, or *Which customers are showing early signals of churn risk?*—require sophisticated analytics engineering to solve.

This platform bridges that gap by implementing a complete local analytics data stack:
1. **Commercial Data Simulator:** A correlated B2B SaaS generator synthesizing Stripe-style billing histories, feature usage telemetry, and customer support patterns.
2. **Relational Data Warehouse:** A PostgreSQL 15 database running locally inside Docker with optimized primary keys, foreign keys, and indices.
3. **Analytics Engineering Engine:** A Python-based database compiler compiling SQL views and materialized views sequentially to build MRR movement waterfalls, customer cohorts, and health risk profiles.
4. **Business Intelligence Application:** A premium, dark-mode Streamlit dashboard that visualizes company recurring revenue growth, cohort heatmaps, and churn playbooks.

---

## 🏗️ Technical Architecture & Data Flow

```mermaid
graph TD
    A[Python Behavioral Simulator] -->|Faker / NumPy / Pandas| B(12 Raw Billing & Usage CSVs)
    B -->|scripts/load_data.py| C[(PostgreSQL 15: raw schema)]
    C -->|scripts/build_analytics.py| D[(PostgreSQL 15: analytics schema)]
    D -->|CTEs / SQL Window Functions| E[Interactive Streamlit Dashboard]
    
    style A fill:#4F46E5,stroke:#312E81,stroke-width:2px,color:#fff
    style B fill:#10B981,stroke:#064E3B,stroke-width:2px,color:#fff
    style C fill:#F59E0B,stroke:#78350F,stroke-width:2px,color:#fff
    style D fill:#EC4899,stroke:#701A75,stroke-width:2px,color:#fff
    style E fill:#06B6D4,stroke:#164E63,stroke-width:2px,color:#fff
```

### The Analytical Engine (SQL Models Hierarchy)
The `analytics` layer translates raw billing logs into high-value decision-ready assets:
* **`customer_overview`:** Consolidated customer profile combining lifetime invoice stats, billing tier, segment, and current MRR.
* **`mrr_movement_report` (⭐ Core Model):** A point-in-time state machine that classifies every customer-month into one of six mutually exclusive categories: `new`, `expansion`, `contraction`, `reactivation`, `churned`, or `unchanged` by comparing historical months using partition-lag functions.
* **`monthly_revenue_overview`:** Computes company-wide aggregate MRR, ARR, NRR, GRR, ARPA, and active logo counts by month.
* **`cohort_retention`:** Tracks monthly user and revenue decay metrics over a 24-month horizon using a triangle retention matrix.
* **`customer_health_scores`:** Computes a composite health score (0–100) per active customer based on usage trends (30%), payment histories (25%), support severity (20%), account tenure (15%), and feature breadth (10%).
* **`churn_risk_segments`:** Flags at-risk customers (`critical`, `high`, `medium`) and triggers automated recommendations.

---

## 📊 Dashboard Visuals Showcase

Capture high-quality dark-mode screenshots from the running Streamlit dashboard to populate these showcases:

| Dashboard Page | Visual Representation & Insights |
|---|---|
| **Revenue & ARR Overview** | *[Insert `docs/screenshots/revenue_overview.png`]* <br> Visualizes Ending MRR, ARR, Active Logo counts, and Net/Gross Retention Trends. |
| **Cohort Retention Heatmap** | *[Insert `docs/screenshots/cohort_analysis.png`]* <br> Displays dynamic triangle retention matrices tracking logo decay over time. |
| **Customer Churn Analysis** | *[Insert `docs/screenshots/churn_analysis.png`]* <br> Identifies churn trends and correlations between payment failures and attrition. |
| **At-Risk Customer Health** | *[Insert `docs/screenshots/customer_health.png`]* <br> Provides CSM teams with interactive health scores and proactive playbooks. |

*See the [Screenshots Guide](docs/screenshots/README.md) for step-by-step instructions on capturing these visuals.*

---

## ⚡ Quick-Start & Local Setup

### Prerequisites
* **Docker Desktop** installed and active.
* **Python 3.10+** with `pip` package manager.

### 1. Install Pinned Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
*(Default credentials are set up for out-of-the-box local operation on port `5433` to prevent conflicts with local databases)*

### 3. Spin Up PostgreSQL Database Container
```bash
docker compose up -d
docker compose ps
# Verify the container status shows "healthy"
```

### 4. Generate & Load Synthetic Datasets
```bash
# Generate 50,000+ Stripe-style mock rows (Jan 2024 - Dec 2025)
python scripts/generate_mock_data.py

# Create the raw tables schema
docker exec -i saas-platform-postgres-1 psql -U saas_user -d saas_platform < sql/schema/01_create_schema.sql

# Load generated data into raw tables
python scripts/load_data.py
```

### 5. Compile the Analytics Schema
Run the automated schema compiler which executes all analytical models in their correct topological order:
```bash
python scripts/build_analytics.py
```

### 6. Verify & Validate Analytics Data Quality
Execute the automated SQL data quality validation suite containing 23 business and technical assertions:
```bash
python scripts/build_analytics.py  # Validation runs at compilation end
# Or execute manually:
psql postgresql://saas_user:saas_pass@localhost:5433/saas_platform -f sql/validation/02_validate_analytics.sql
```

### 7. Launch the Interactive Streamlit App
```bash
streamlit run dashboards/streamlit_app.py
```
*Your browser will automatically open to `http://localhost:8501` to show the active application.*

---

## 📂 Project Directory Structure

```
saas-revenue-churn-intelligence/
├── .github/workflows/       # GitHub Actions CI configurations (automated compilation tests)
├── dashboards/              # Interactive Streamlit front-end application
│   ├── pages/               # Multi-page dashboard layouts
│   ├── streamlit_app.py     # Streamlit entrypoint
│   └── style.py             # Custom premium dark-mode styling tokens
├── docs/                    # Deep technical and analytical guides
│   ├── screenshots/         # Placeholder and guides for dashboard captures
│   ├── analytics_layer.md   # SQL State-Machine design specifications
│   ├── architecture.md      # Systems engineering blueprint
│   ├── dashboard_guide.md   # Operational manual for front-end users
│   ├── database_setup.md    # Detailed database installation instructions
│   └── metrics.md           # Authoritative definitions of NRR/GRR/MRR
├── scripts/                 # Core Python scripts (Data compiler, generator, loader)
├── sql/                     # Raw DDL & Analytical SQL transformations
│   ├── analytics/           # Step-by-step SQL transformations (Views/Materialized Views)
│   ├── schema/              # DDL schema definitions (customers, subscriptions, payments)
│   └── validation/          # Data Quality (DQ) assertions and validation models
├── .env.example             # Example environment file for local execution
├── docker-compose.yml       # Production-ready PostgreSQL container definition
├── LICENSE                  # Open-source MIT License
├── README.md                # Premium Portfolio Showcase
└── requirements.txt         # Pinned python packages
```

---

## 💼 Recruitment Optimization Strategy

If you are a job seeker presenting this repository to recruiters or portfolio reviewers, use the following customized highlights to describe your achievements:

### For Analytics Engineers (dbt, SQL, Data Modeling focus)
* **Resume Bullet:** *Built a B2B SaaS revenue analytics stack modeling Stripe-style billing data for 1,500+ accounts (~50k rows) on PostgreSQL. Authored a topologically-ordered Python compiler to materialise 8 SQL layers, reducing analytical compilation time to under 1 second.*
* **Resume Bullet:** *Developed an MRR movement state machine in PostgreSQL using advanced SQL window functions (partition-lag windowing), classifying monthly accounts into 6 mutually-exclusive recurring categories to track ARR, NRR (avg. 103%), and GRR (avg. 98.6%).*
* **Interview Pitch:** *"In this project, I tackled the complexity of event-based Stripe billing datasets. Real-world billing data isn't organized by month; it's a stream of invoices, upgrades, and cancellations. I constructed a dbt-inspired topological data pipeline that transforms these raw records into a point-in-time subscription ledger, modeling NRR, GRR, and a composite customer health metric entirely in SQL."*

### For Data Analysts (BI, Dashboards, Insights focus)
* **Resume Bullet:** *Designed and deployed an interactive B2B customer retention dashboard using Streamlit and Plotly, displaying interactive cohort retention triangles, MRR waterfall charts, and proactive account health trackers.*
* **Resume Bullet:** *Formulated a composite customer health scoring model (0-100) using weighted product usage, invoice payment rates, and support ticket severity to flag at-risk accounts, reducing critical dunning churn risk.*
* **Interview Pitch:** *"My goal was to create an interactive dashboard that goes beyond simple static reporting. By connecting a custom Streamlit dashboard to our SQL analytics warehouse, I built a proactive risk playbook for Customer Success. Teams can instantly filter customer segments, analyze cohort logo decay, and view a prioritized list of high-risk customers alongside their specific health scores and dunning flags."*

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
