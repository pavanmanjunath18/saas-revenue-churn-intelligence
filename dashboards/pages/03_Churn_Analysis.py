"""Churn Analysis — who churns, when, and from which segments."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from db import query
from style import C, SEGMENT_COLORS, chart_layout

st.set_page_config(page_title="Churn Analysis", page_icon="📉", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
churn_by_seg = query("""
    SELECT month, segment,
           COUNT(DISTINCT CASE WHEN movement_type = 'churned' THEN customer_id END) AS churned_customers,
           ROUND(SUM(CASE WHEN movement_type = 'churned' THEN prev_mrr_usd ELSE 0 END), 2) AS churned_mrr_usd,
           COUNT(DISTINCT CASE WHEN current_mrr_cents > 0 THEN customer_id END) AS active_customers
    FROM analytics.mrr_movement_report
    GROUP BY month, segment
    ORDER BY month, segment
""")
churn_by_seg["month"] = churn_by_seg["month"].astype(str)

monthly = query("""
    SELECT month, customer_churn_rate_pct, nrr_pct,
           churned_mrr_usd, churned_customers, active_customers
    FROM analytics.monthly_revenue_overview
    ORDER BY month
""")
monthly["month"] = monthly["month"].astype(str)

churned = query("""
    SELECT mr.customer_id, mr.company_name, mr.segment, mr.industry,
           mr.month AS churn_month, mr.plan_name,
           mr.prev_mrr_usd AS lost_mrr_usd, mr.prev_mrr_cents
    FROM analytics.mrr_movement_report mr
    WHERE mr.movement_type = 'churned'
    ORDER BY mr.prev_mrr_cents DESC
""")
churned["churn_month"] = churned["churn_month"].astype(str)

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Churn Analysis")
st.caption("Which customers cancelled, in which months, and what revenue was lost? Segment and industry breakdown.")
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
avg_churn    = monthly["customer_churn_rate_pct"].mean()
total_lost   = churned["lost_mrr_usd"].sum()
total_events = len(churned)
latest_nrr   = monthly.iloc[-1]["nrr_pct"]
avg_lost_per = total_lost / total_events if total_events else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Churned MRR",      f"${total_lost:,.0f}")
c2.metric("Churn Events",           f"{total_events:,}")
c3.metric("Avg MRR Lost / Churn",   f"${avg_lost_per:,.0f}")
c4.metric("Avg Monthly Churn Rate", f"{avg_churn:.2f}%")
c5.metric("Latest NRR",             f"{latest_nrr:.1f}%")

st.divider()

# ── Churn rate + churned MRR trend ────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Monthly Customer Churn Rate")
    st.caption("Percentage of active customers lost each month.")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["customer_churn_rate_pct"],
        mode="lines", fill="tozeroy",
        line=dict(color=C["red"], width=2),
        fillcolor="rgba(220,38,38,0.07)",
        hovertemplate="%{y:.2f}%<extra>Churn rate</extra>",
    ))
    fig1.add_hline(y=avg_churn, line_dash="dot", line_color=C["amber"], line_width=1.5,
                   annotation_text=f"avg {avg_churn:.2f}%",
                   annotation_font_size=10, annotation_font_color=C["amber"],
                   annotation_position="bottom right")
    lay = chart_layout(height=280)
    lay.update({"yaxis": {**lay.get("yaxis", {}), "ticksuffix": "%"}})
    fig1.update_layout(**lay)
    st.plotly_chart(fig1, use_container_width=True)

with col_r:
    st.subheader("Monthly Churned MRR")
    st.caption("Dollar value of subscriptions cancelled each month.")
    fig2 = go.Figure(go.Bar(
        x=monthly["month"], y=monthly["churned_mrr_usd"],
        marker_color=C["red"], marker_line_width=0, opacity=0.8,
        hovertemplate="$%{y:,.0f}<extra>Churned MRR</extra>",
    ))
    lay2 = chart_layout(height=280)
    lay2.update({"yaxis": {**lay2.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"}})
    fig2.update_layout(**lay2)
    st.plotly_chart(fig2, use_container_width=True)

# ── Churn by segment ──────────────────────────────────────────────────────────
st.subheader("Churned MRR by Segment")
st.caption("Stacked view of MRR loss per segment over time.")

seg_pivot = churn_by_seg.pivot(
    index="month", columns="segment", values="churned_mrr_usd"
).fillna(0)

fig3 = go.Figure()
for seg, color in [("smb", SEGMENT_COLORS["smb"]),
                   ("mid_market", SEGMENT_COLORS["mid_market"]),
                   ("enterprise", SEGMENT_COLORS["enterprise"])]:
    if seg in seg_pivot.columns:
        label = seg.replace("_", " ").title()
        fig3.add_trace(go.Bar(
            x=seg_pivot.index, y=seg_pivot[seg], name=label,
            marker_color=color, marker_line_width=0,
            hovertemplate="$%{y:,.0f}<extra>" + label + "</extra>",
        ))
lay3 = chart_layout(height=300)
lay3.update({"barmode": "stack", "showlegend": True,
             "yaxis": {**lay3.get("yaxis", {}), "tickprefix": "$", "tickformat": ",.0f"}})
fig3.update_layout(**lay3)
st.plotly_chart(fig3, use_container_width=True)

# ── Industry + plan breakdown ─────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Churned MRR by Industry")
    st.caption("Top 10 industries by total MRR lost.")
    by_ind = (churned.groupby("industry")["lost_mrr_usd"]
              .sum().sort_values(ascending=True).tail(10).reset_index())
    fig4 = go.Figure(go.Bar(
        x=by_ind["lost_mrr_usd"], y=by_ind["industry"],
        orientation="h",
        marker_color=C["red"], marker_line_width=0, opacity=0.8,
        hovertemplate="$%{x:,.0f}<extra>%{y}</extra>",
    ))
    lay4 = chart_layout(height=320)
    lay4.update({
        "xaxis": {**lay4.get("xaxis", {}), "tickprefix": "$", "tickformat": ",.0f"},
        "yaxis": {**lay4.get("yaxis", {}), "showgrid": False},
        "margin": {**lay4.get("margin", {}), "l": 120},
    })
    fig4.update_layout(**lay4)
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("Churn Distribution by Segment")
    st.caption("MRR value lost per segment as share of total churn.")
    by_seg = churned.groupby("segment")["lost_mrr_usd"].sum().reset_index()
    by_seg["label"] = by_seg["segment"].str.replace("_", " ").str.title()
    fig5 = go.Figure(go.Pie(
        labels=by_seg["label"],
        values=by_seg["lost_mrr_usd"],
        hole=0.55,
        marker=dict(colors=[SEGMENT_COLORS.get(s, C["accent"]) for s in by_seg["segment"]],
                    line=dict(color="white", width=2)),
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    fig5.update_layout(
        paper_bgcolor="white", height=320,
        margin=dict(t=12, b=12, l=20, r=20),
        showlegend=False,
        font=dict(family="sans-serif", color=C["text_muted"]),
    )
    st.plotly_chart(fig5, use_container_width=True)

st.info("SMB segment accounts for the majority of churn events, though enterprise churn "
        "carries higher MRR impact per event. Monitoring high-MRR accounts (> $500 MRR) "
        "proactively reduces revenue exposure.")

# ── Largest churned accounts ──────────────────────────────────────────────────
st.subheader("Largest Churned Accounts")
st.caption("Top cancellations by MRR value — highest revenue impact first.")
st.dataframe(
    churned[["company_name", "segment", "industry", "plan_name",
             "churn_month", "lost_mrr_usd"]]
    .rename(columns={
        "company_name": "Company", "segment": "Segment", "industry": "Industry",
        "plan_name": "Plan", "churn_month": "Month", "lost_mrr_usd": "MRR Lost ($)",
    })
    .head(20)
    .style.format({"MRR Lost ($)": "${:,.2f}"}),
    use_container_width=True, hide_index=True,
)
