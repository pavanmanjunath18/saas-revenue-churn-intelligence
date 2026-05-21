# Engineering Roadmap — SaaS Revenue & Churn Intelligence Platform

---

## Phase 0 — Architecture & Planning ✅ IN PROGRESS

**Goal:** Think before building. All architectural decisions made before first line of code.

**Deliverables:**
- [x] Folder structure
- [x] architecture.md
- [x] schema.md
- [x] metrics.md
- [x] roadmap.md
- [x] decisions.md
- [x] backlog.md
- [x] interview_notes.md

**Exit criteria:** Every table, metric, and model is fully defined before Phase 1 begins.

---

## Phase 1 — Synthetic Data Generation

**Goal:** Generate 12 realistic CSV files that behave like real SaaS billing data.

**Key scripts:**
- `scripts/generate_data.py` — main generator
- `scripts/validate_data.py` — sanity checks before DB load

**Behavioral patterns to implement:**
- 500 customers across 3 segments (SMB/mid-market/enterprise)
- 24 months of history (cohort-based)
- Realistic churn rates per segment
- Correlated signals: usage decline → churn, support spikes → churn
- Annual vs. monthly billing mix (~30% annual)
- Upgrade/downgrade/reactivation events

**Exit criteria:** Data passes all validation checks. MRR waterfall is plausible. Churn rates match configured targets.

---

## Phase 2 — PostgreSQL Schema & Data Load

**Goal:** Raw tables live in PostgreSQL. Data loaded cleanly.

**Deliverables:**
- `sql/schema/001_create_tables.sql` — DDL for all 12 tables
- `sql/seeds/` — reference data (products, plans)
- `scripts/load_data.py` — CSV → PostgreSQL loader
- `docker-compose.yml` — local PostgreSQL environment

**Exit criteria:** All 12 tables populated. Row counts match generator output. Foreign key integrity passes.

---

## Phase 3 — SQL Analytics Layer

**Goal:** Build the 8 analytics models. MRR movement logic must be airtight.

**Deliverables (in build order):**

1. `customer_overview` — baseline customer enrichment
2. `subscription_details` — enriched subscription view
3. `invoice_details` — invoice + payment status
4. `monthly_revenue_overview` — MRR/ARR aggregated by month
5. `mrr_movement_report` — **the core model** — new/expansion/contraction/churn/reactivation
6. `cohort_retention` — triangle retention matrix
7. `customer_churn_risk` — risk signals per customer
8. `customer_health_scores` — composite health score

**SQL tests (per model):**
- Each customer appears exactly once per month in MRR movement
- Movement types are mutually exclusive
- NRR calculation cross-validates against movement report
- Cohort row sums to 100% at month 0

**Exit criteria:** All 8 models pass their SQL tests. MRR movement validated manually for 10 sample customers.

---

## Phase 4 — Dashboards & Visualization

**Goal:** Business stakeholders can see the data. Recruiters can see the dashboards.

**Dashboards:**

1. **Revenue Overview** — MRR, ARR, ARPA, NRR by month
2. **MRR Waterfall** — visual breakdown of new/expansion/contraction/churn by month
3. **Churn Analysis** — churn rate by segment, churn reasons, leading indicators
4. **Cohort Retention** — triangle heatmap
5. **Customer Health** — health score distribution, at-risk customer list

**Tools:** Tableau Public (shareable) or Power BI (embedded)

**Exit criteria:** All 5 dashboards published. Screenshots captured for README.

---

## Phase 5 — Polish, Deployment, GitHub Optimization

**Goal:** Project is recruiter-ready and publicly shareable.

**Deliverables:**
- Clean README.md with architecture diagram, screenshots, SQL samples
- Docker Compose fully working (`docker compose up` → everything runs)
- GitHub Actions CI (schema validation + data quality checks on push)
- Live demo PostgreSQL hosted (optional — Railway or Supabase)
- Architecture diagram (draw.io or Mermaid)
- Interview prep notes finalized

**Exit criteria:** A recruiter can clone the repo, run `docker compose up`, and have a working analytics database in under 5 minutes.

---

## Backlog / Future Phases

See `backlog.md` for items intentionally deferred.

- Predictive churn model (scikit-learn / SHAP feature importance)
- dbt integration (replace raw SQL with dbt models + tests)
- Streaming simulation (Kafka → PostgreSQL)
- REST API over analytics layer (FastAPI)
