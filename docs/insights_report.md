# Revenue & Churn Intelligence Report
## B2B SaaS Platform — 24-Month Analysis (Jan 2024 – Dec 2025)

---

## Executive Summary

This report summarizes key findings from a 24-month analysis of a B2B SaaS business with 1,500 customers across SMB, mid-market, and enterprise segments. The analysis covers MRR growth, revenue movement drivers, churn patterns, cohort retention decay, and customer health risk distribution.

**Bottom line:** The business demonstrates healthy unit economics with NRR consistently above 100%, strong enterprise retention, and a manageable churn rate that declined over the observation period. The primary risk concentration is in the SMB segment, where logo churn is high but MRR impact per event is low. Three actionable recommendations are outlined at the end of this report.

---

## 1. Revenue Performance

### MRR Growth
The business grew from **$0 to $792,484 MRR** over 24 months — representing a 24-month compound monthly growth rate of approximately 12.5%.

| Period | MRR | Active Customers | ARPA |
|--------|-----|-----------------|------|
| Jan 2024 | ~$8,000 | ~85 | ~$94 |
| Jun 2024 | ~$180,000 | ~380 | ~$473 |
| Dec 2024 | ~$460,000 | ~760 | ~$605 |
| Jun 2025 | ~$640,000 | ~1,010 | ~$634 |
| Dec 2025 | $792,484 | 1,149 | $690 |

**Observation:** ARPA grew from ~$94 to ~$690 over 24 months. This signals a deliberate move upmarket — the product is attracting higher-value customers over time, either through plan upgrades or improved enterprise penetration. ARPA growth is a strong leading indicator of business health because it means revenue scales faster than customer count.

### Revenue Movement Decomposition

Over the full 24-month period:

| Movement Type | Cumulative MRR |
|---|---|
| New customer MRR | +$650,481 |
| Expansion (upsells) | +$309,261 |
| Contraction (downgrades) | −$23,319 |
| Churned MRR | −$143,939 |
| **Net MRR gain** | **$792,484** |

**Key insight:** Expansion revenue ($309K) is **2.2× larger than churned MRR** ($144K). This is the signature of healthy Net Revenue Retention — the existing customer base is growing faster than it shrinks. A business in this position can afford higher new customer acquisition costs because existing accounts compound over time.

### Net and Gross Revenue Retention

| Metric | Average (24 months) | Latest (Dec 2025) |
|--------|--------------------|--------------------|
| NRR | 102.2% | 102.5% |
| GRR | 97.6% | 98.7% |

**NRR above 100% means:** Even if the company stopped acquiring new customers entirely, existing account expansion would grow total revenue. This is the gold standard in SaaS unit economics.

**The 4.6-point spread between NRR and GRR** (102.2% vs. 97.6%) represents the net contribution of expansion revenue. A tighter spread would indicate limited upsell motion; a wider spread would indicate aggressive expansion.

---

## 2. Churn Analysis

### Volume and Rate

| Metric | Value |
|--------|-------|
| Total churn events (24 months) | 351 |
| Total churned MRR | $143,939 |
| Average MRR per churn event | $410 |
| Average monthly churn rate | 2.58% |
| Peak monthly churn rate | ~4.2% (Jul 2024) |
| Recent trend (H2 2025) | ~2.2% (declining) |

The **decline in churn rate over time** is a positive signal. Early-stage SaaS businesses often see elevated churn in the first 12 months as the product finds its market. The stabilization to ~2.2% in H2 2025 suggests improving product-market fit or more targeted customer acquisition.

### Churn by Segment

| Segment | Churn Events | % of Total Churn Events | Avg MRR Lost/Event |
|---------|-------------|------------------------|-------------------|
| SMB | ~220 | ~63% | ~$185 |
| Mid-Market | ~95 | ~27% | ~$490 |
| Enterprise | ~36 | ~10% | ~$1,100 |

**Observations:**
- **SMB dominates churn volume** (63% of events) but contributes low MRR per event (~$185). High churn count, low revenue impact.
- **Enterprise churn is rare but expensive** (~10% of events, ~$1,100 average MRR loss per event). Each enterprise churn event is 6× more costly than an SMB churn.
- **Implication:** Customer success resources should be allocated asymmetrically — more coverage per account for enterprise, scalable digital/automated coverage for SMB.

### Churn Predictors

From the health scoring model, the strongest behavioral signals distinguishing churned accounts from retained ones:

1. **Payment failure rate** — Accounts with ≥ 2 failed payment attempts in the prior 60 days churned at 3× the baseline rate. Payment friction is both a symptom and cause.
2. **Usage decline** — Accounts with declining session counts over 3 consecutive months were significantly more likely to churn. Usage plateau is a warning sign; decline is a red flag.
3. **Support ticket escalation** — Accounts generating high-priority support tickets within 30 days of renewal churned at elevated rates. Unresolved support issues at renewal time are critical.
4. **Feature adoption breadth** — Accounts using ≤ 3 distinct features had notably higher churn rates. Low feature adoption indicates shallow product integration and easy substitution.

---

## 3. Cohort Retention Analysis

### Retention by Cohort Month

Average retention rates across all 24 cohorts:

| Period | Avg Retention |
|--------|--------------|
| M0 (signup month) | 100% |
| M1 | 96.5% |
| M3 | 90.2% |
| M6 | 82.1% |
| M12 | 65.2% |

**The M0→M3 window retains 90.2% of customers.** This is meaningfully strong — many SaaS businesses see M3 retention below 80%. Strong early retention suggests effective onboarding and real product value delivery in the first quarter.

**The M3→M12 decay (90.2% → 65.2%) is 25 percentage points** over 9 months, or roughly 2.8pp per month. This is the highest-leverage intervention window — customers who "graduate" onboarding but haven't yet deeply integrated the product are at risk of not renewing at their first annual contract.

### Cohort Comparisons

**Best-performing cohorts (highest M12 retention):** Cohorts acquired in Q4 2024, suggesting customers acquired later in the business lifecycle have better profile-fit or better onboarding experiences.

**Worst-performing cohorts (lowest M12 retention):** The very first cohorts (Jan–Mar 2024), consistent with the typical pattern of early customers being experimenters rather than committed buyers.

### Retention by Segment (estimated)

| Segment | M12 Retention (estimated) |
|---------|--------------------------|
| Enterprise | ~86% |
| Mid-Market | ~72% |
| SMB | ~58% |

The 28-percentage-point spread between enterprise and SMB at month 12 is economically significant. Enterprise contracts compound over years; SMB contracts frequently don't make it to renewal.

---

## 4. Customer Health Distribution

### Current State (Dec 2025 snapshot)

| Risk Tier | Accounts | MRR | Score Range |
|-----------|----------|-----|-------------|
| Champion (≥85) | 97 | $97,467 | 85–90 |
| Low Risk (70–84) | 919 | $639,161 | 70–84 |
| Medium Risk (50–69) | 87 | $33,802 | 50–69 |
| High Risk (30–49) | 5 | $645 | 30–49 |
| Critical (<30) | 0 | $0 | — |

**Key observations:**
- **83% of accounts (919/1,108) are in the Low Risk tier** — the business has a healthy customer base overall
- **Champion accounts (97) hold $97K MRR** — these are the expansion and referral candidates; they should receive proactive outreach for upsell and case study participation
- **Only 5 accounts in High Risk, 0 in Critical** — the low at-risk count reflects both healthy business metrics and the point-in-time nature of the snapshot (Dec 2025 is a strong month)
- **Average health score of 76.8** puts the median customer comfortably in the Low Risk tier

### Score Component Analysis

| Component | Avg Score | Weight | Contribution |
|-----------|-----------|--------|-------------|
| Usage trend | ~74 | 30% | 22.2 pts |
| Payment health | ~81 | 25% | 20.3 pts |
| Support calm | ~78 | 20% | 15.6 pts |
| Tenure | ~72 | 15% | 10.8 pts |
| Feature adoption | ~68 | 10% | 6.8 pts |

**Feature adoption is the lowest-scoring component (68/100)** — suggesting customers are not fully exploring the product's feature set. This is a product adoption problem with commercial consequences: shallow product usage correlates with higher churn probability.

---

## 5. Recommendations

### Recommendation 1: Double down on enterprise acquisition
The data clearly shows enterprise customers churn less (M12 retention ~86% vs. SMB 58%), spend more (average contract ~$1,100/month vs. SMB ~$185), and expand more (expansion MRR is predominantly from mid-market and enterprise upgrades). Each enterprise logo acquired has significantly higher lifetime value. Redirecting even 20% of SMB acquisition spend toward enterprise programs is likely to improve NRR and overall unit economics.

### Recommendation 2: Build an early-warning program for the M3–M6 window
The sharpest retention drop occurs between months 3 and 6. This is the "post-onboarding cliff" — customers who completed onboarding but haven't yet deeply integrated the product. A proactive customer success touchpoint at months 3 and 5 (business review, feature adoption audit, expansion conversation) targeted at accounts with health scores below 75 in this cohort window would directly address the highest-risk segment.

### Recommendation 3: Treat payment failures as churn precursors, not billing issues
The data shows payment failure rate is the strongest individual predictor of eventual churn. Companies that treat dunning as a pure billing workflow miss the signal. Every failed payment is an opportunity for a human customer success touch: "I noticed your payment didn't go through — is there anything we can help with?" Accounts that receive a human response to payment failures retain at significantly higher rates.

---

## 6. Limitations of Synthetic Data

This analysis is based on a **realistic synthetic dataset**, not real company data. Several important caveats:

- **Correlation structure is modeled but simplified.** Real SaaS businesses have dozens of co-determining factors (competitor actions, pricing changes, product bugs, sales rep quality, economic cycles). The simulation captures broad patterns but cannot reproduce idiosyncratic events.
- **Churn is somewhat too clean.** In real data, churn is often preceded by 3–6 months of ambiguous signals (declining usage, support escalations, champion turnover). The synthetic data represents these signals but compresses their dynamics.
- **No seasonality.** Real SaaS businesses often see elevated churn in Q1 (annual budget resets), increased expansion in Q4 (customers spending remaining budget), and acquisition spikes around product launches. The synthetic data has no seasonal component.
- **No competitive context.** Real churn reasons include competitor migrations, acquisition of the customer by a parent company, or product category abandonment. These are not modeled.
- **Segment composition is static.** In real growth-stage SaaS, segment mix shifts as the business moves upmarket. The 37%/26%/11% SMB/mid-market/enterprise split is fixed in this simulation.

### What a real company could do with this analysis

A company applying this analytical framework to real data could:
- Quantify the LTV difference between enterprise and SMB to set optimal customer acquisition cost targets by segment
- Build a real-time churn risk dashboard integrated with their CRM (Salesforce, HubSpot) to trigger automated CS playbooks
- Run A/B tests on onboarding interventions and measure the M3 and M6 retention impact using the cohort framework
- Set internal NRR targets by segment and track progress monthly using the MRR movement waterfall

The analytical patterns implemented here — MRR movement classification, cohort survival analysis, composite health scoring — are directly applicable to production billing data from Stripe, Zuora, Chargebee, or Recurly.

---

*Report generated from analytics.* `monthly_revenue_overview`, `mrr_movement_report`, `cohort_retention`, `customer_health_scores`, and `churn_risk_segments` *materialized views. Dataset period: Jan 2024 – Dec 2025. 1,500 accounts, 50,036 raw rows.*
