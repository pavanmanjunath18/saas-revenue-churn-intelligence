# V2 Improvement Plan — SaaS Revenue & Churn Intelligence Platform

**Status:** Approved for implementation  
**Scope:** Portfolio publication polish — no new features, cleanup and presentation only

---

## 1. Refined Product Positioning

### What this project is

A **B2B SaaS analytics platform** that models subscription revenue, churn, retention, and customer health using realistic synthetic billing and usage data. It demonstrates the complete analytics engineering workflow from raw event data to business-ready metrics — the same workflow used at companies like Stripe, Recurly, Zuora, and their customers.

### What it demonstrates

- Translating raw billing events into point-in-time subscription metrics (the core challenge of SaaS analytics)
- Implementing industry-standard SaaS KPIs (MRR, ARR, NRR, GRR, ARPA, cohort retention) in SQL
- Building a customer health scoring system that operationalizes churn risk
- Shipping a live, interactive analytics dashboard connected to a production cloud database

### Positioning statement

> "A subscription analytics platform that solves the event-sourcing problem inherent to SaaS billing data — turning raw invoices, payments, and usage logs into decision-ready revenue intelligence."

### What to avoid saying

| Don't say | Say instead |
|---|---|
| "Basic SQL project" | "Analytics engineering project modeling SaaS subscription metrics" |
| "Streamlit demo" | "Interactive analytics dashboard deployed on Streamlit Cloud" |
| "Fake data" | "Realistic synthetic billing data generated with statistically correlated customer behavior" |
| "Interview prep exercise" | "End-to-end analytics platform covering data generation through deployment" |
| "Tutorial project" | "Production-style analytics stack with validation, CI, and live deployment" |

---

## 2. Stronger End-to-End Project Narrative

The project should be read as a **single coherent story**, not a collection of components. The narrative arc:

1. **The Problem** — SaaS companies can't answer basic revenue questions from raw billing data because it's event-sourced and non-continuous
2. **The Data** — A realistic simulation of 1,500 B2B customers across SMB/mid-market/enterprise segments, generating 50K+ correlated billing events over 24 months
3. **The Engineering** — A PostgreSQL analytics layer that transforms those events into a subscription ledger using SQL window functions, CTEs, and materialized views
4. **The Intelligence** — Five business questions answered through interactive visualizations: revenue growth, movement drivers, churn patterns, cohort retention, and customer health
5. **The Deployment** — Live on Streamlit Cloud connected to Neon PostgreSQL, accessible to anyone with a browser

This narrative should be explicit in the README, not implied.

---

## 3. Improved Dashboard Flow and Storytelling

### Recommended page order (already correct)
1. **Home** → "here's the overall business picture"
2. **Revenue Overview** → "how is MRR/ARR trending?"
3. **MRR Waterfall** → "what's driving that trend?"
4. **Churn Analysis** → "who is leaving and why?"
5. **Cohort Retention** → "how long do we keep customers?"
6. **Customer Health** → "who's at risk right now?"

### Storytelling improvements
- Home page should reference specific numbers ("MRR grew 98% over 24 months") not generic labels
- Each page should open with a 1-sentence business question in the `st.caption()`, not a technical description
- Add a `st.sidebar.markdown()` note showing the data date range ("Jan 2024 – Dec 2025")

### Navigation fix
- Home page cards should use `st.page_link()` for actual navigation (Streamlit 1.31+)
- Sidebar app name should read "Revenue Intelligence" not "streamlit app"

---

## 4. README Restructuring Plan

### Current problems
- Leads with dense technical language before explaining the value
- No real screenshots embedded (placeholder comments remain)
- Resume bullets mixed into README body — should be a separate section at the bottom
- No clear "What does this do?" paragraph for a non-technical reader

### New structure
```
1. Title + tagline (1 line)
2. Live demo badge + tech stack badges
3. 3-sentence problem statement
4. Screenshot row (3 images side by side)
5. Key metrics callout (NRR 102.2%, MRR $792K, etc.)
6. What's inside (5 bullet features)
7. Architecture diagram (Mermaid)
8. Dashboard pages (with screenshots)
9. Data model summary
10. Analytics models table
11. Setup instructions (collapsible sections)
12. Deployment instructions
13. Project structure (tree)
14. Insights summary
15. Resume bullets (clearly labeled)
16. Future improvements
17. License
```

---

## 5. Visual Assets Plan

### Assets to create
| Asset | Format | Location | Status |
|---|---|---|---|
| Dashboard home screenshot | PNG | `docs/assets/01_home.png` | ✅ Done |
| Revenue Overview screenshot | PNG | `docs/assets/02_revenue_overview.png` | ✅ Done |
| MRR Waterfall screenshot | PNG | `docs/assets/03_mrr_waterfall.png` | ✅ Done |
| Churn Analysis screenshot | PNG | `docs/assets/04_churn_analysis.png` | ✅ Done |
| Cohort Retention screenshot | PNG | `docs/assets/05_cohort_retention.png` | ✅ Done |
| Customer Health screenshot | PNG | `docs/assets/06_customer_health.png` | ✅ Done |
| Architecture diagram | Mermaid in README | README.md | ✅ Done |
| Data pipeline diagram | Mermaid in README | README.md | ✅ Done |

### Screenshot usage in README
- 3-image row at the top (home, revenue, waterfall) as the hero visual
- Individual screenshots next to each dashboard page description

---

## 6. GitHub Presentation Improvements

### Repository metadata
- **Description:** "B2B SaaS analytics platform: MRR movement, cohort retention, churn analysis, and customer health scoring. Python · PostgreSQL · SQL · Streamlit"
- **Topics/tags:** `analytics`, `saas`, `postgresql`, `streamlit`, `python`, `sql`, `data-engineering`, `mrr`, `churn-analysis`, `cohort-analysis`
- **Website:** Link to live Streamlit Cloud deployment

### Files to remove/privatize before publication
- `docs/interview_notes.md` — too informal, looks like personal prep notes
- `docs/backlog.md` — empty stub
- `docs/decisions.md` — rewrite as proper ADR or remove

### Files to add
- `docs/project_audit.md` (this document's companion) ✅
- `docs/insights_report.md` — analyst-style deliverable showing findings
- `tests/test_data_quality.py` — at least one pytest to fill the empty `tests/` directory

---

## 7. Technical Polish Improvements

### High priority
- [ ] Fix sidebar app name: update `.streamlit/config.toml` with `[browser] serverAddress`
- [ ] Delete all empty scaffold directories
- [ ] Add `tests/test_data_quality.py` with basic assertions
- [ ] Remove `docs/interview_notes.md` from public repo
- [ ] Fix CI — remove reference to `build_analytics.py` which isn't the build script

### Medium priority
- [ ] Add `st.page_link()` navigation to home page cards
- [ ] Add data range note to sidebar
- [ ] Pin Python version in CI to 3.11

### Low priority (defer to v3)
- [ ] Convert `sys.path.insert` hacks to proper package imports
- [ ] Add `Makefile` with `make setup`, `make refresh`, `make dashboard` targets
- [ ] Add `REFRESH MATERIALIZED VIEW` script

---

## 8. Documentation Improvements

### Files to rewrite
| File | Action |
|---|---|
| `README.md` | Full rewrite with screenshots, narrative, clean structure |
| `docs/project_summary.md` | Keep but update to match new positioning |
| `docs/analytics_layer.md` | Remove "phase" language, add diagram |
| `docs/database_setup.md` | Consolidate with README setup section |

### Files to create
| File | Purpose |
|---|---|
| `docs/insights_report.md` | Analyst-style findings report from the synthetic data |
| `docs/project_audit.md` | This document |
| `docs/v2_improvement_plan.md` | This document |

### Files to delete
| File | Reason |
|---|---|
| `docs/interview_notes.md` | Unprofessional in public repo |
| `docs/backlog.md` | Low-quality stub |

---

## 9. What Should Remain Unchanged

The following components are well-built and should **not** be touched:

- `scripts/generate_mock_data.py` — sophisticated correlated data generator, works correctly
- `scripts/load_data.py` — type-safe batch loader with correct error handling
- `sql/schema/01_create_schema.sql` — clean DDL with proper constraints and indexes
- `sql/analytics/05_mrr_movement_report.sql` — the core model, correct and validated
- `sql/analytics/04_monthly_revenue_overview.sql` — correct NRR/GRR implementation
- `sql/analytics/07_customer_health_scores.sql` — weighted multi-factor scoring, well-structured
- `sql/analytics/08_churn_risk_segments.sql` — clean risk tier logic
- `sql/validation/02_validate_analytics.sql` — 23 assertions, all correct
- `dashboards/db.py` — clean connection chain with cache_resource
- `dashboards/style.py` — lightweight color token system
- All five dashboard page files — correct queries, good chart choices
- `docker-compose.yml` — production-ready PostgreSQL container config
- `scripts/setup_cloud_db.sh` — clean one-command cloud setup
- `.github/workflows/ci.yml` — good CI structure (needs minor fix for `build_analytics.py` reference)
- `requirements.txt` — comprehensive and correct after consolidation

---

## 10. Recommended Future Enhancements

These are real improvements worth implementing in a v3 — each would materially strengthen the project's technical story:

### Analytics depth
- **Segment-level NRR/GRR** — break out retention by SMB/mid-market/enterprise to show the enterprise premium effect
- **Logo retention vs revenue retention** — track customer count separately from MRR to show the difference
- **Churn prediction model** — a scikit-learn logistic regression using health score features as input; adds ML dimension without overcomplicating the project

### Engineering maturity
- **dbt conversion** — replace the SQL files with dbt models (`ref()`, `source()`, `schema.yml` tests). Dramatically increases recognizability to analytics engineering hiring managers.
- **Makefile** — `make setup` / `make refresh` / `make test` interface
- **Great Expectations** or **dbt tests** for data quality instead of raw SQL assertions

### Platform features
- **Alerting simulation** — a Python script that identifies customers who crossed a risk tier threshold this month and "would send" a CS team notification
- **Historical health scores** — snapshot health scores monthly so trend analysis ("this customer's health dropped 15 points this month") becomes possible
- **API layer** — a FastAPI endpoint serving the health scores as JSON, making it feel like a real data product
