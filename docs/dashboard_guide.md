# Streamlit Dashboard User Guide

Welcome to the **SaaS Revenue & Churn Intelligence Platform** interactive dashboard! 

This guide serves as a manual for business stakeholders, executive sponsors, and analytics engineers using the dashboard to monitor company performance, analyze cohort metrics, and take proactive actions to reduce churn.

---

## Getting Started

To launch the dashboard locally, make sure you have loaded the synthetic data and compiled the analytics models (see [Database Setup Guide](database_setup.md)). Then, run:

```bash
streamlit run dashboards/streamlit_app.py
```

The app will open automatically in your default browser at `http://localhost:8501`.

---

## Dashboard Structure & Pages

The dashboard is structured into **five core analytics pages** accessible from the sidebar. Each page addresses a specific business challenge.

```
📊 Revenue Intelligence (Home Page)
├── 📈 Revenue Overview (MRR/ARR growth, NRR & GRR, segment splits)
├── 🌊 MRR Waterfall (Point-in-time MRR movement components)
├── 📉 Churn Analysis (Logo and Revenue Churn, segment and plan splits)
├── 🔁 Cohort Retention (Monthly customer cohort lifecycle decay matrix)
└── ❤️ Customer Health (Real-time risk scoring, account lists, action plans)
```

---

## Page Walkthroughs & Rationale

### 1. Home Page / Overview Hub
* **Objective:** Give executives an instant snapshot of the health of the B2B SaaS platform.
* **Key KPIs Displayed:** 
  * **Monthly Recurring Revenue (MRR):** Current monthly normalized recurring subscription book.
  * **Annual Run Rate (ARR):** The MRR multiplied by 12, reflecting our annualized growth trajectory.
  * **Active Customers (Logo Count):** Total unique active accounts.
  * **Net Revenue Retention (NRR):** Month-over-month account dollar growth.
  * **Monthly Customer Churn Rate:** Percentage of logos lost in the prior month.
* **Immediate Alerts:** A persistent alert banner fires if any customer is in the `critical` or `high` risk tier, calculating the total dollar MRR at risk.

---

### 2. Revenue Overview Page (`📈 Revenue Overview`)
* **Objective:** Understand long-term growth trends and structural revenue segments.
* **Core Visualizations:**
  * **MRR vs. Active Customers Line Chart:** Secondary-y axis overlaying monthly MRR growth with active logo count over the 24-month horizon.
  * **NRR & GRR Dual-Line Trend:** Tracks NRR (which includes expansion) and GRR (capped at 100%, excluding expansion) over time. This illustrates whether growth relies on new logo acquisition or expansion of the existing book.
  * **MRR Contribution by Segment:** A stacked column chart displaying SMB, Mid-Market, and Enterprise revenue volumes.
  * **ARPA Bar Chart:** Tracks Average Revenue Per Account monthly, highlighting increases in customer ticket value.
  * **Monthly Churn Rate Trend:** A visual timeline displaying Logo Churn with a historical average reference line.

---

### 3. MRR Waterfall Page (`🌊 MRR Waterfall`)
* **Objective:** Break down the structural components of revenue change (Net New MRR) month-over-month.
* **Core Visualizations:**
  * **Interactive Date Slider:** Dynamic select-slider allowing users to narrow down the 24-month horizon.
  * **Point-in-Time MRR Waterfall Chart:** Leverages a relative bar chart to separate monthly gains (`New MRR`, `Expansion MRR`, `Reactivation MRR`) and monthly losses (`Contraction MRR`, `Churned MRR`). A dotted trendline overlays Net New MRR.
  * **Logo Additions & Cancellations:** Side-by-side logo waterfalls showing raw customer gains and losses.
  * **Detailed Monthly Ledger Table:** An expandable data table showing the exact dollar figures behind the waterfall.

---

### 4. Churn Analysis Page (`📉 Churn Analysis`)
* **Objective:** Track churn and pinpoint where logo and revenue leakage is occurring.
* **Core Visualizations:**
  * **Logo vs. Revenue Churn Rate:** Side-by-side time series charts tracking count-based logo churn against value-based revenue churn.
  * **Churn Breakdown by Segment:** Dynamic bar charts showcasing how churn rates vary across customer tiers (SMB, Mid-Market, Enterprise).
  * **Churn by Billing Interval & Plan Tier:** Visual splits identifying if monthly plans or specific plan types (e.g., Growth vs. Business) suffer from higher cancellation rates.

---

### 5. Cohort Retention Page (`🔁 Cohort Retention`)
* **Objective:** Model the long-term decay of monthly customer cohorts over a 24-month horizon.
* **Core Visualizations:**
  * **Interactive Heatmap Matrix:** A standard cohort retention triangle displaying months active (1 to 24) on the X-axis and cohort signup months on the Y-axis. The matrix is color-coded from bright green (100% retention) to deep red (decayed cohorts).
  * **Interactive Segment Selector:** Instantly recalculates the cohort matrix for specific tiers, demonstrating how Enterprise cohorts remain flat (best-in-class retention) while SMB cohorts experience faster decay.

---

### 6. Customer Health Page (`❤️ Customer Health`)
* **Objective:** Translate high-level metrics into actionable, customer-level intelligence.
* **Core Components:**
  * **Segment Risk Split:** Heatmap bar showing customer counts by segment and risk tier.
  * **Actionable Critical Risk List:** SURFACES any customer in the `critical` or `high` risk tier. Lists their name, segment, MRR, composite health score, usage trend, and ticket status.
  * **Operational Action Playbook:** Proposes standard corporate procedures for at-risk accounts, e.g.:
    * *Critical Risk:* Immediate Customer Success Manager (CSM) call, billing check, or product session.
    * *High Risk:* Feature walkthrough and priority support resolution.
    * *Medium Risk:* Automatic email automation check-in.
