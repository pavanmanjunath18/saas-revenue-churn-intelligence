# Project Audit — SaaS Revenue & Churn Intelligence Platform

**Date:** May 2026  
**Scope:** Full repository review covering data engineering, analytics SQL, dashboard, documentation, and GitHub presentation  
**Purpose:** Internal quality review before portfolio publication

---

## 1. Current Strengths

### Data Engineering
- **Realistic data generator** produces correlated billing behavior (cancellations follow payment failures, enterprise customers churn less than SMB) — this is more sophisticated than most portfolio data generators that produce random uniform noise
- **Correct schema design** with 12 normalized tables, proper PKs/FKs, enum constraints on categoricals, and composite indexes on high-cardinality filter columns
- **50,036 rows** across realistic entity types — products, plans, customers, subscriptions, invoices, payments, refunds, usage, support tickets — covering the full billing domain
- **Type-safe CSV loader** explicitly converts NumPy types, handles NaT/NaN, uses `ON CONFLICT DO NOTHING` for idempotent reloads

### SQL Analytics Layer
- **MRR movement state machine** (`mrr_movement_report`) is the strongest technical piece — correctly uses customer-specific spine trimming to prevent false reactivation classification, LAG window functions for period-over-period comparison, and classifies all six movement types (new, expansion, contraction, reactivation, churned, unchanged)
- **NRR and GRR computed correctly** — NRR includes expansion, GRR capped at 100%, both computed from the movement report rather than re-derived independently
- **Health scoring** uses a weighted composite with five independent signals (usage trend, payment health, support load, tenure, feature breadth) — a credible multi-factor model
- **23 data quality assertions** in the validation suite, all passing — demonstrates engineering discipline
- **Topological execution order** in `99_run_all_analytics.sql` with explicit dependency management

### Dashboard
- All five pages answer a distinct business question — not just "show the data" but structured around revenue, waterfall, churn, cohorts, and health
- Real interactive features: date range slider on MRR Waterfall, period slider on cohort, segment/tier drill-down on customer health, radar chart for individual account comparison
- **Deployed and live** on Streamlit Cloud connected to Neon PostgreSQL — not just a local demo

### Infrastructure
- Docker Compose for local PostgreSQL with health checks
- Cloud DB setup script (`setup_cloud_db.sh`) for one-command remote deployment
- `db.py` connection priority chain (Streamlit secrets → .env → default) handles all environments cleanly
- GitHub Actions CI runs syntax checks and data generation on every push

---

## 2. Areas That Feel Unfinished or Overly Simplistic

### Dashboard UX
- **Sidebar label still says "streamlit app"** — no custom app name configured in `.streamlit/config.toml`
- **No page icons in sidebar nav** — pages show as plain text; Streamlit supports icons via `page_icon` in `set_page_config` but sidebar nav labels don't reflect them
- **Home page navigation cards are static HTML** — they display titles and descriptions but aren't clickable buttons that navigate to pages
- **No loading state** — on cold start or slow connection, charts appear blank for 2–4 seconds with no spinner feedback
- **Customer Health drill-down** shows recommended action as plain text inside an `st.info()` box — could be more visually structured

### Data Model Gaps
- **`data/raw/` and `data/processed/` directories are empty** — these placeholder folders serve no purpose and create confusion about the data flow
- **`sql/models/`, `sql/seeds/`, `sql/tests/` directories are empty** — leftover scaffold folders that were never used
- **`notebooks/` directory is completely empty** — suggests exploratory analysis was planned but never done
- **`architecture/diagrams/` directory is empty** — intended for diagrams that were never created

### Documentation
- **README screenshots are placeholder text** — `[Insert screenshot]` comments remain in the original README structure; the deployed version has no visual evidence
- **`docs/interview_notes.md`** is too informal for a public repo — reads as internal prep notes, not a portfolio artifact
- **`docs/backlog.md`** and `docs/roadmap.md` are low-quality stub files (38 and 123 lines) with no real content
- **`docs/decisions.md`** describes technical decisions in first-person conversational tone — feels like a work diary rather than an ADR (Architecture Decision Record)
- **`docs/schema.md`** is good but not linked from the README
- **`dashboards/churn_analysis/`, `dashboards/cohort_analysis/`, `dashboards/revenue_overview/`** are empty directories — leftover from an earlier iteration

### Technical Gaps
- **No `__init__.py` in dashboards/** — `db.py` and `style.py` are imported via `sys.path.insert` hacks instead of a proper package structure
- **`scripts/build_analytics.py`** exists but is referenced in CI (`py_compile` check) yet not used in the current setup flow — `99_run_all_analytics.sql` is used instead
- **`sql/schema/03_validation_queries.sql`** naming is confusing — the `03_` prefix suggests it belongs in the schema creation flow but it's actually a standalone validation script
- **No `.env.example`** that users can actually copy — the current `.env.example` at root duplicates what's already in `docker-compose.yml`

---

## 3. Components That Need Refinement for Polished Presentation

| Component | Issue | Priority |
|---|---|---|
| README | No real screenshots embedded; heavy on bullet lists, light on narrative | High |
| Sidebar app name | Shows "streamlit app" instead of project name | High |
| Empty directories | `notebooks/`, `architecture/diagrams/`, `data/raw/`, `data/processed/`, `sql/models/`, etc. | Medium |
| `docs/interview_notes.md` | Too informal for public visibility | High |
| Home page nav cards | Non-clickable; don't behave as navigation | Medium |
| Architecture diagram | Referenced in README but doesn't exist as a real file | High |
| `scripts/build_analytics.py` | Referenced in CI but not documented or used in setup | Low |

---

## 4. Documentation Gaps

- **No `docs/dashboard_guide.md` for end users** — there is a file by this name but it's sparse (96 lines) and reads as a developer note rather than a user guide
- **No explanation of the synthetic data limitations** anywhere in the public-facing docs — important for professional framing
- **`docs/analytics_layer.md`** is excellent (266 lines, detailed) but references `phase 3` which is an internal label that means nothing to an external reader
- **No insights report** — the project builds all this analytics infrastructure but never surfaces a sample "what did we find" narrative
- **No diagram of the data model / ERD** — schema.md describes tables in prose but no visual
- **Setup instructions split across README, `docs/database_setup.md`, and `scripts/`** — a first-time user has to read multiple files to understand the full flow

---

## 5. Opportunities to Improve Visual Storytelling

- **The cohort retention heatmap** is the strongest visual — it should be the hero image in the README, not buried in page 4
- **The MRR waterfall** clearly tells a growth story ($0 → $792K over 24 months) — this should be front-and-center in the README narrative
- **Health score distribution histogram** (Customer Health page) is a clean bell curve centered around 76.8 — the shape itself tells a story about customer portfolio quality
- **The NRR chart staying consistently above 100%** is a powerful signal — worth calling out explicitly in the README as a key insight
- Architecture should be shown as a clean linear pipeline diagram (not just a Mermaid text block)
- A data model / ERD diagram would significantly increase technical credibility for recruiters reviewing the repo

---

## 6. UX/UI Improvements for the Dashboard

| Improvement | Impact |
|---|---|
| Set custom sidebar app name via `st.set_page_config(page_title=...)` in all pages (already done) but configure `.streamlit/config.toml` with a proper title | Visual polish |
| Make home page nav cards link to their pages using `st.page_link()` (Streamlit 1.31+) | Functionality |
| Add `st.spinner("Loading data...")` wrapper around initial query calls | Perceived performance |
| Replace `st.info()` for insight callouts with a custom styled `st.markdown()` block | Consistency |
| Add a "last updated" timestamp to the sidebar showing when data was last loaded | Trust signal |
| Improve the Customer Health radar chart title — currently shows full company name which truncates on small screens | Readability |

---

## 7. Technical Improvements That Increase Credibility

- **Add a `conftest.py` + at least one pytest test** in `tests/` — an empty `tests/` directory is a red flag for experienced reviewers
- **Pin exact Python version** in CI (`python-version: "3.11"` not `"3.10"`) and add a `pyproject.toml` or `.python-version` file
- **Convert `sys.path.insert` hacks to proper relative imports** — or add an `__init__.py` to make `dashboards/` a package
- **Add `REFRESH MATERIALIZED VIEW` logic** — currently materialized views are only built once; a `refresh_analytics.sh` script would make the system feel production-ready
- **Add row count validation** at the end of the loader script — confirm expected counts against known values
- **Rename `99_run_all_analytics.sql`** — the `99_` prefix is an artifact of alphabetical sorting; rename to `build_analytics_layer.sql` or add a `Makefile`

---

## 8. Priority Fixes Before Portfolio Publication

Ordered by impact on recruiter/reviewer impression:

1. **Rewrite README** with real screenshots embedded, clean narrative, and no placeholder text
2. **Delete empty directories** (`notebooks/`, `architecture/diagrams/`, `data/raw/`, `data/processed/`, `sql/models/`, `sql/seeds/`, `sql/tests/`, `dashboards/churn_analysis/`, `dashboards/cohort_analysis/`, `dashboards/revenue_overview/`)
3. **Remove or privatize `docs/interview_notes.md`** — it's unprofessional in a public portfolio
4. **Create architecture and data flow diagrams** as Mermaid in README
5. **Update sidebar app name** — fix the "streamlit app" label
6. **Write `docs/insights_report.md`** — a sample analyst deliverable showing what the platform found
7. **Create `docs/project_audit.md`** and `docs/v2_improvement_plan.md` (this document)
8. **Add at least one test file** to `tests/` so the directory isn't empty
9. **Fix CI** — `build_analytics.py` is referenced but not the actual build script used

---

## 9. Optional Enhancements for Future Iterations

These are genuinely good ideas but would constitute significant new features — not appropriate for a cleanup pass:

- **dbt integration** — convert the SQL models to dbt format with `schema.yml` tests, `sources.yml`, and `ref()` dependencies. This would make the project significantly more recognizable to data engineering hiring managers.
- **Segment-level NRR/GRR breakdown** — currently only company-wide; per-segment retention curves would add analytical depth
- **Predictive churn score** — a simple logistic regression or gradient boosting model on health score features would add an ML dimension
- **Email/Slack alert simulation** — a script that "would send" alerts for customers crossing risk tier thresholds
- **Makefile** — a single `make setup`, `make refresh`, `make dashboard` interface for the whole project
- **dbt-style documentation** — auto-generated lineage graph showing model dependencies
- **Historical snapshots** — currently health scores are point-in-time; a daily snapshot table would enable health score trend analysis
