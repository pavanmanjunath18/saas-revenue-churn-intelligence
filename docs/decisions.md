# Architecture Decision Log — SaaS Revenue & Churn Intelligence Platform

Each decision records what we chose, why, and what we rejected. This is interview-defensible reasoning.

---

## ADR-001: Store MRR as monthly-normalized value on subscription

**Decision:** Store `mrr_cents` directly on the `subscriptions` table as a monthly-normalized value.

**Why:** MRR movement analysis requires comparing month-over-month MRR per customer. If we stored raw price and billing interval separately and derived MRR at query time, every analytics query would require the same normalization logic (`CASE WHEN billing_interval = 'annual' THEN price / 12 ELSE price END`), creating risk of inconsistency.

**Rejected alternative:** Derive MRR at query time from `plans.price_cents` and `subscriptions.billing_interval`.

**Tradeoff:** Denormalization. Updating plan prices requires updating subscriptions too.

**Interview angle:** "In real Stripe-style systems, the billed amount can differ from the plan price due to discounts, trials, and custom pricing. Storing MRR on the subscription captures the *actual* contracted value, not the list price."

---

## ADR-002: Use subscription_items for add-ons, not separate subscriptions

**Decision:** Model add-ons and seat expansions as `subscription_items` rows under one `subscription`, not as separate subscription records.

**Why:** Real SaaS billing systems (Stripe, Chargebee) use this model. It lets us sum `subscription_items.total_price_cents` to get total subscription MRR, and track individual add-on usage separately.

**Rejected alternative:** One subscription per product/add-on per customer.

**Tradeoff:** Slightly more complex MRR aggregation, but more accurate representation.

---

## ADR-003: MRR movement as a monthly snapshot, not event-sourced

**Decision:** Compute MRR movement by comparing monthly snapshots (current vs. prior month MRR), not by processing subscription change events in order.

**Why:** Event sourcing is more accurate for intra-month changes, but significantly more complex to implement and explain. Snapshot-based movement is the industry-standard approach for most SaaS analytics platforms and is what every interviewer expects.

**Rejected alternative:** Event-sourced MRR (track every upgrade/downgrade event with timestamps, reconstruct MRR changes from events).

**Tradeoff:** Snapshot approach misses multiple movements within the same month (e.g., upgrade then immediate downgrade). Acceptable for this project.

---

## ADR-004: Cohort defined by first subscription month, not signup date

**Decision:** A customer's cohort is the month of their first active subscription, not the month they created an account.

**Why:** Free signups that never convert have no MRR. Cohort analysis is about revenue retention. Using subscription start date makes the cohort relevant to revenue behavior.

**Rejected alternative:** Cohort = signup date (account creation date).

**Tradeoff:** A customer who signs up in January but starts paying in March joins the March cohort — which is counterintuitive but analytically correct for revenue questions.

**Interview angle:** "If you define cohorts by signup date, free-to-paid conversion delays will make your early retention numbers look worse than they are. I define cohorts by first payment date."

---

## ADR-005: Store monetary values in cents (integers)

**Decision:** All monetary values stored as INTEGER (cents), not DECIMAL or FLOAT.

**Why:** Floating-point arithmetic errors compound over large aggregations. `$99.99 * 12 = $1199.88` in theory but floating point can produce $1199.8800000000001. Cents avoid this entirely.

**Pattern:** Divide by 100 only at the presentation layer (in SQL models or dashboards).

---

## ADR-006: Soft deletes on customers

**Decision:** Use `is_deleted` flag rather than hard-deleting customer rows.

**Why:** Historical revenue and churn analysis requires customers to exist even after they cancel. A hard delete would corrupt cohort retention calculations.

---

## ADR-007: SQL models over ORM for analytics layer

**Decision:** Analytics models are plain SQL files (dbt-inspired), not Python/SQLAlchemy queries.

**Why:** The analytics layer is inherently relational and SQL is the right tool. Python ORMs are designed for transactional workloads, not analytical aggregations with window functions, CTEs, and GROUP BYs. SQL is also the language recruiters expect for this type of work.

---

## ADR-008: Synthetic data generated with behavioral profiles, not pure random

**Decision:** Customers have assigned behavioral profiles (healthy / at_risk / churned) that govern their usage and support patterns.

**Why:** Pure random data produces analytically boring results — no patterns, no signals, nothing to discover. Behavioral profiles allow us to build a churn risk model that actually works and make the data tell a business story.

**Profile → behavior mappings:**
- healthy: usage stable/growing, few support tickets, on-time payments
- at_risk: usage declining, more support tickets, occasional payment failures
- churned: usage declines sharply 2–4 months before `canceled_at`, billing tickets spike
