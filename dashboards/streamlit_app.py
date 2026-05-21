"""SaaS Revenue & Churn Intelligence — home page."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from db import query
from style import C

st.set_page_config(
    page_title="Revenue Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Fetch summary stats ───────────────────────────────────────────────────────
summary = query("""
    SELECT month, total_mrr_usd, arr_usd, active_customers,
           nrr_pct, grr_pct, customer_churn_rate_pct
    FROM analytics.monthly_revenue_overview
    ORDER BY month DESC LIMIT 2
""")
risk_counts = query("""
    SELECT risk_tier, COUNT(*) AS n
    FROM analytics.churn_risk_segments
    GROUP BY risk_tier
""")

latest = summary.iloc[0]
prev   = summary.iloc[1]
risk   = risk_counts.set_index("risk_tier")["n"].to_dict()

# ── Page header ───────────────────────────────────────────────────────────────
st.title("SaaS Revenue & Churn Intelligence")
st.caption("24-month simulation · 1,500 customers · PostgreSQL analytics layer · 8 SQL models")
st.divider()

# ── KPI metrics ───────────────────────────────────────────────────────────────
mrr_delta = latest.total_mrr_usd - prev.total_mrr_usd
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Monthly Recurring Revenue", f"${latest.total_mrr_usd:,.0f}",
          f"${mrr_delta:+,.0f} vs prior month")
c2.metric("Annual Run Rate", f"${latest.arr_usd:,.0f}")
c3.metric("Active Customers", f"{int(latest.active_customers):,}",
          f"{int(latest.active_customers - prev.active_customers):+} vs prior month")
c4.metric("Net Revenue Retention", f"{latest.nrr_pct:.1f}%",
          f"{latest.nrr_pct - prev.nrr_pct:+.1f}pp vs prior month")
c5.metric("Monthly Churn Rate", f"{latest.customer_churn_rate_pct:.2f}%",
          f"{latest.customer_churn_rate_pct - prev.customer_churn_rate_pct:+.2f}pp vs prior month")

st.divider()

# ── Navigation cards ──────────────────────────────────────────────────────────
st.subheader("Dashboard Pages")
pages = [
    ("📈 Revenue Overview",   "How is MRR/ARR trending? What are NRR and GRR?"),
    ("🌊 MRR Waterfall",      "Where is revenue coming from and going to each month?"),
    ("📉 Churn Analysis",     "Who is churning, when, and from which segments?"),
    ("🔁 Cohort Retention",   "How long do cohorts retain at months 3, 6, 12, 24?"),
    ("❤️ Customer Health",    "Which active customers are at churn risk right now?"),
]

cols = st.columns(len(pages))
for col, (title, question) in zip(cols, pages):
    with col:
        st.info(f"**{title}**\n\n{question}")

# ── Risk alert ────────────────────────────────────────────────────────────────
high_risk = risk.get("high", 0) + risk.get("critical", 0)
if high_risk > 0:
    at_risk_mrr = query("""
        SELECT ROUND(SUM(mrr_usd), 0) AS total
        FROM analytics.churn_risk_segments
        WHERE risk_tier IN ('high', 'critical')
    """).iloc[0]["total"]
    st.warning(
        f"**{high_risk} customers** are in the high or critical risk tier, "
        f"representing **${at_risk_mrr:,.0f}** in MRR at risk. "
        f"Review the Customer Health page for recommended actions."
    )

st.divider()
st.caption("Data: synthetic B2B SaaS simulation · Stack: Python · PostgreSQL 15 · Streamlit · Plotly · 8 SQL models in analytics schema")
