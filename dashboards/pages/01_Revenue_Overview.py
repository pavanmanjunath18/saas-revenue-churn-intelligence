"""Revenue Overview — MRR/ARR trend, NRR/GRR retention, segment split."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db import query
from style import C, SEGMENT_COLORS, chart_layout

st.set_page_config(page_title="Revenue Overview", page_icon="📈", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
df = query("""
    SELECT month, total_mrr_usd, arr_usd, active_customers, arpa_usd,
           nrr_pct, grr_pct, customer_churn_rate_pct,
           smb_mrr_usd, mid_market_mrr_usd, enterprise_mrr_usd
    FROM analytics.monthly_revenue_overview
    ORDER BY month
""")
df["month"] = df["month"].astype(str)
latest, prev = df.iloc[-1], df.iloc[-2]

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Revenue Overview")
st.caption("Monthly MRR/ARR trajectory, net and gross retention, and segment-level contribution.")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
mrr_d   = latest.total_mrr_usd - prev.total_mrr_usd
nrr_d   = latest.nrr_pct - prev.nrr_pct
grr_d   = latest.grr_pct - prev.grr_pct
churn_d = latest.customer_churn_rate_pct - prev.customer_churn_rate_pct

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MRR", f"${latest.total_mrr_usd:,.0f}", f"${mrr_d:+,.0f}")
c2.metric("ARR", f"${latest.arr_usd:,.0f}")
c3.metric("NRR", f"{latest.nrr_pct:.1f}%", f"{nrr_d:+.1f}pp")
c4.metric("GRR", f"{latest.grr_pct:.1f}%", f"{grr_d:+.1f}pp")
c5.metric("Churn Rate", f"{latest.customer_churn_rate_pct:.2f}%", f"{churn_d:+.2f}pp")

st.divider()

# ── MRR trend ─────────────────────────────────────────────────────────────────
st.subheader("Monthly Recurring Revenue")
st.caption("24-month trajectory — total MRR with active customer count overlay.")

fig_mrr = make_subplots(specs=[[{"secondary_y": True}]])
fig_mrr.add_trace(go.Scatter(
    x=df["month"], y=df["total_mrr_usd"],
    name="MRR", mode="lines",
    line=dict(color=C["accent"], width=2.5),
    fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
    hovertemplate="$%{y:,.0f}<extra>MRR</extra>",
), secondary_y=False)
fig_mrr.add_trace(go.Scatter(
    x=df["month"], y=df["active_customers"],
    name="Active customers", mode="lines",
    line=dict(color=C["text_muted"], width=1.5, dash="dot"),
    hovertemplate="%{y:,}<extra>Customers</extra>",
), secondary_y=True)

lay = chart_layout(height=300)
lay.update({"showlegend": True,
            "yaxis":  {**lay.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"},
            "yaxis2": {"showgrid": False, "tickfont": dict(size=11, color=C["text_faint"]),
                       "zeroline": False}})
fig_mrr.update_layout(**lay)
st.plotly_chart(fig_mrr, use_container_width=True)

mrr_growth = (df.iloc[-1].total_mrr_usd / df.iloc[0].total_mrr_usd - 1) * 100
st.info(f"MRR grew **{mrr_growth:.0f}%** over the 24-month period, "
        f"from **${df.iloc[0].total_mrr_usd:,.0f}** to **${df.iloc[-1].total_mrr_usd:,.0f}**.")

# ── NRR / GRR ─────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Net & Gross Revenue Retention")
    st.caption("NRR > 100% signals expansion outpaces churn. GRR excludes upsell.")
    fig_ret = go.Figure()
    fig_ret.add_trace(go.Scatter(
        x=df["month"], y=df["nrr_pct"], name="NRR",
        line=dict(color=C["green"], width=2.5), mode="lines",
        hovertemplate="%{y:.1f}%<extra>NRR</extra>",
    ))
    fig_ret.add_trace(go.Scatter(
        x=df["month"], y=df["grr_pct"], name="GRR",
        line=dict(color=C["accent"], width=2, dash="dash"), mode="lines",
        hovertemplate="%{y:.1f}%<extra>GRR</extra>",
    ))
    fig_ret.add_hline(y=100, line_dash="dot", line_color=C["border"], line_width=1.5,
                      annotation_text="100%", annotation_font_size=10,
                      annotation_font_color=C["text_faint"],
                      annotation_position="bottom right")
    lay2 = chart_layout(height=280)
    lay2.update({"showlegend": True,
                 "yaxis": {**lay2.get("yaxis", {}), "ticksuffix": "%", "range": [85, 115]}})
    fig_ret.update_layout(**lay2)
    st.plotly_chart(fig_ret, use_container_width=True)

with col_r:
    st.subheader("MRR by Customer Segment")
    st.caption("Revenue contribution from SMB, mid-market, and enterprise accounts.")
    fig_seg = go.Figure()
    for col_name, label, color in [
        ("smb_mrr_usd",        "SMB",        SEGMENT_COLORS["smb"]),
        ("mid_market_mrr_usd", "Mid-Market", SEGMENT_COLORS["mid_market"]),
        ("enterprise_mrr_usd", "Enterprise", SEGMENT_COLORS["enterprise"]),
    ]:
        fig_seg.add_trace(go.Bar(
            x=df["month"], y=df[col_name], name=label,
            marker_color=color, marker_line_width=0,
            hovertemplate="$%{y:,.0f}<extra>" + label + "</extra>",
        ))
    lay3 = chart_layout(height=280)
    lay3.update({"barmode": "stack", "showlegend": True,
                 "yaxis": {**lay3.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"}})
    fig_seg.update_layout(**lay3)
    st.plotly_chart(fig_seg, use_container_width=True)

st.info(f"NRR averaged **{df.nrr_pct.mean():.1f}%** across the period — consistently above 100%, "
        f"meaning expansion revenue outweighs churn. "
        f"GRR averaged **{df.grr_pct.mean():.1f}%**, reflecting strong base retention before upsell effects.")

# ── ARPA + churn ──────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Average Revenue Per Account")
    st.caption("ARPA trend reveals pricing and mix changes over time.")
    fig_arpa = go.Figure(go.Bar(
        x=df["month"], y=df["arpa_usd"],
        marker_color=C["accent"], marker_line_width=0, opacity=0.85,
        hovertemplate="$%{y:,.2f}<extra>ARPA</extra>",
    ))
    lay4 = chart_layout(height=260)
    lay4.update({"yaxis": {**lay4.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"}})
    fig_arpa.update_layout(**lay4)
    st.plotly_chart(fig_arpa, use_container_width=True)

with col4:
    st.subheader("Monthly Customer Churn Rate")
    st.caption("Percentage of active customers lost each month.")
    fig_churn = go.Figure(go.Scatter(
        x=df["month"], y=df["customer_churn_rate_pct"],
        mode="lines", fill="tozeroy",
        line=dict(color=C["red"], width=2),
        fillcolor="rgba(220,38,38,0.07)",
        hovertemplate="%{y:.2f}%<extra>Churn rate</extra>",
    ))
    avg_churn = df["customer_churn_rate_pct"].mean()
    fig_churn.add_hline(y=avg_churn, line_dash="dot", line_color=C["amber"], line_width=1.5,
                        annotation_text=f"avg {avg_churn:.2f}%",
                        annotation_font_size=10, annotation_font_color=C["amber"],
                        annotation_position="bottom right")
    lay5 = chart_layout(height=260)
    lay5.update({"yaxis": {**lay5.get("yaxis", {}), "ticksuffix": "%"}})
    fig_churn.update_layout(**lay5)
    st.plotly_chart(fig_churn, use_container_width=True)
