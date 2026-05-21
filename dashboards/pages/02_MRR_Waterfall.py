"""MRR Waterfall — movement component breakdown by month."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from db import query
from style import C, chart_layout

st.set_page_config(page_title="MRR Waterfall", page_icon="🌊", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
df = query("""
    SELECT month, total_mrr_usd,
           new_mrr_usd, expansion_mrr_usd, reactivation_mrr_usd,
           contraction_mrr_usd, churned_mrr_usd, net_new_mrr_usd,
           new_customers, expansion_customers, contraction_customers,
           churned_customers, reactivation_customers
    FROM analytics.monthly_revenue_overview
    ORDER BY month
""")
df["month"] = df["month"].astype(str)

# ── Page header ───────────────────────────────────────────────────────────────
st.title("MRR Waterfall")
st.caption("Where is revenue being added and lost each month? New, expansion, contraction, and churn broken out.")
st.divider()

# ── Date filter ───────────────────────────────────────────────────────────────
months = df["month"].tolist()
col_filter, _ = st.columns([2, 3])
with col_filter:
    start, end = st.select_slider(
        "Date range",
        options=months,
        value=(months[0], months[-1]),
        label_visibility="collapsed",
    )
dff = df[(df["month"] >= start) & (df["month"] <= end)].copy()

# ── KPI row ───────────────────────────────────────────────────────────────────
total_new   = dff["new_mrr_usd"].sum()
total_exp   = dff["expansion_mrr_usd"].sum()
total_cont  = dff["contraction_mrr_usd"].sum()
total_churn = dff["churned_mrr_usd"].sum()
net_net     = total_new + total_exp - total_cont - total_churn

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total New MRR",     f"${total_new:,.0f}")
c2.metric("Total Expansion",   f"${total_exp:,.0f}")
c3.metric("Total Contraction", f"${total_cont:,.0f}")
c4.metric("Total Churned MRR", f"${total_churn:,.0f}")
c5.metric("Net MRR Change",    f"${net_net:,.0f}")

st.divider()

# ── Revenue movement chart ────────────────────────────────────────────────────
st.subheader("Revenue Movement by Month")
st.caption("Green bars add to MRR; red bars subtract. The dotted line shows net new MRR per month.")

fig = go.Figure()
for col_name, name, color in [
    ("new_mrr_usd",          "New",          C["green"]),
    ("expansion_mrr_usd",    "Expansion",    "rgba(22,163,74,0.45)"),
    ("reactivation_mrr_usd", "Reactivation", "rgba(22,163,74,0.25)"),
]:
    fig.add_trace(go.Bar(
        x=dff["month"], y=dff[col_name], name=name,
        marker_color=color, marker_line_width=0,
        hovertemplate="$%{y:,.0f}<extra>" + name + "</extra>",
    ))

for col_name, name, color in [
    ("contraction_mrr_usd", "Contraction", "rgba(220,38,38,0.45)"),
    ("churned_mrr_usd",     "Churned",     C["red"]),
]:
    fig.add_trace(go.Bar(
        x=dff["month"], y=-dff[col_name], name=name,
        marker_color=color, marker_line_width=0,
        hovertemplate="$%{y:,.0f}<extra>" + name + "</extra>",
    ))

fig.add_trace(go.Scatter(
    x=dff["month"], y=dff["net_new_mrr_usd"],
    name="Net new MRR", mode="lines+markers",
    line=dict(color=C["text"], width=1.5, dash="dot"),
    marker=dict(size=4, color=C["text"]),
    hovertemplate="$%{y:,.0f}<extra>Net new</extra>",
))

lay = chart_layout(height=360)
lay.update({"barmode": "relative", "showlegend": True,
            "yaxis": {**lay.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"}})
fig.add_hline(y=0, line_color=C["border"], line_width=1)
fig.update_layout(**lay)
st.plotly_chart(fig, use_container_width=True)

net_pos_months = (dff["net_new_mrr_usd"] > 0).sum()
st.info(f"**{net_pos_months} of {len(dff)} months** show positive net new MRR. "
        f"New customer revenue (${total_new:,.0f}) is the primary growth driver, "
        f"with expansion (**${total_exp:,.0f}**) providing a meaningful secondary contribution. "
        f"Churn (**${total_churn:,.0f}**) is the largest drag.")

# ── Customer count movement ───────────────────────────────────────────────────
st.subheader("Customer Count Movement")
st.caption("Net change in active customer count each month.")

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=dff["month"], y=dff["new_customers"],
    name="New customers", marker_color=C["green"], marker_line_width=0,
    hovertemplate="%{y}<extra>New</extra>",
))
fig2.add_trace(go.Bar(
    x=dff["month"], y=-dff["churned_customers"],
    name="Churned customers", marker_color=C["red"], marker_line_width=0,
    hovertemplate="%{y}<extra>Churned</extra>",
))
fig2.add_hline(y=0, line_color=C["border"], line_width=1)

lay3 = chart_layout(height=280)
lay3.update({"barmode": "relative", "showlegend": True})
fig2.update_layout(**lay3)
st.plotly_chart(fig2, use_container_width=True)

# ── Monthly detail table ──────────────────────────────────────────────────────
with st.expander("Monthly breakdown — detailed table"):
    display = dff[[
        "month", "total_mrr_usd", "new_mrr_usd", "expansion_mrr_usd",
        "contraction_mrr_usd", "churned_mrr_usd", "net_new_mrr_usd",
    ]].rename(columns={
        "month": "Month", "total_mrr_usd": "Total MRR",
        "new_mrr_usd": "New", "expansion_mrr_usd": "Expansion",
        "contraction_mrr_usd": "Contraction", "churned_mrr_usd": "Churned",
        "net_new_mrr_usd": "Net New",
    })
    fmt = {c: "${:,.0f}" for c in display.columns if c != "Month"}
    st.dataframe(
        display.sort_values("Month", ascending=False).style.format(fmt),
        use_container_width=True, hide_index=True,
    )
