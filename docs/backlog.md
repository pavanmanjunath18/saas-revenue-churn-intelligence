# Backlog — SaaS Revenue & Churn Intelligence Platform

Items intentionally deferred. Prioritized for future phases.

---

## High Priority (Phase 5+)

- [ ] Predictive churn model (scikit-learn, logistic regression + gradient boosting)
- [ ] SHAP feature importance on churn model — which signals matter most?
- [ ] dbt integration — replace SQL files with dbt models, tests, docs
- [ ] Docker Compose full stack — postgres + data loader in one `docker compose up`
- [ ] GitHub Actions CI — run SQL tests on every push
- [ ] Architecture diagram (Mermaid or draw.io)
- [ ] Live hosted demo database (Railway or Supabase)

## Medium Priority

- [ ] FastAPI layer over analytics schema — expose metrics as a REST API
- [ ] Email alert simulation — trigger alert when customer health score drops below 40
- [ ] Slack webhook integration — post weekly MRR summary to simulated Slack channel
- [ ] Expansion revenue analysis — identify expansion patterns by segment and product
- [ ] Customer acquisition cost (CAC) simulation — add marketing spend table
- [ ] LTV:CAC ratio by segment

## Low Priority / Nice to Have

- [ ] Kafka streaming simulation — replace batch CSV load with streaming ingestion
- [ ] Great Expectations data quality framework integration
- [ ] Superset or Metabase as open-source dashboard alternative to Tableau
- [ ] Multi-currency support (EUR, GBP)
- [ ] Tax calculation simulation per geography

## Intentionally Out of Scope

- Real Stripe API integration (synthetic data is intentional)
- Authentication / multi-user access (not an application)
- Mobile dashboard
