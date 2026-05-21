"""Customer Health — composite health scores, risk tiers, at-risk accounts."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from db import query
from style import C, SEGMENT_COLORS, chart_layout

st.set_page_config(page_title="Customer Health", page_icon="❤️", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
health = query("""
    SELECT customer_id, company_name, segment, industry, plan_name,
           billing_interval, mrr_usd, health_score,
           usage_score, payment_score, support_score, tenure_score, feature_score,
           tenure_months
    FROM analytics.customer_health_scores
    ORDER BY health_score
""")

risk = query("""
    SELECT customer_id, company_name, segment, industry, plan_name,
           billing_interval, mrr_usd, health_score, risk_tier, risk_flag_count,
           flag_usage_declining, flag_payment_issues, flag_support_overloaded,
           flag_low_feature_adoption, flag_new_customer_risk,
           mrr_at_risk_usd, recommended_action
    FROM analytics.churn_risk_segments
    ORDER BY health_score
""")

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Customer Health")
st.caption("Composite health scores and churn risk tiers for every active account. "
           "Scores combine usage trend, payment history, support load, tenure, and feature adoption.")
st.divider()

# ── Tier config ───────────────────────────────────────────────────────────────
TIER_ORDER  = ["critical", "high", "medium", "low", "champion"]
TIER_COLORS = {
    "critical": "#DC2626", "high": "#EA580C", "medium": "#D97706",
    "low":      "#16A34A", "champion": "#7C3AED",
}
TIER_LABELS = {
    "critical": "Critical  (<30)", "high": "High  (30–49)",
    "medium": "Medium  (50–69)", "low": "Low  (70–84)",
    "champion": "Champion  (≥85)",
}

tier_counts = risk.groupby("risk_tier").agg(
    customers=("customer_id", "count"), mrr=("mrr_usd", "sum")
).reindex([t for t in TIER_ORDER if t in risk["risk_tier"].values])

# ── KPI row ───────────────────────────────────────────────────────────────────
avg_h        = health["health_score"].mean()
at_risk_mrr  = risk[risk["risk_tier"].isin(["critical", "high"])]["mrr_usd"].sum()
at_risk_n    = int(risk["risk_tier"].isin(["critical", "high"]).sum())
champion_n   = int((risk["risk_tier"] == "champion").sum())
champion_mrr = risk[risk["risk_tier"] == "champion"]["mrr_usd"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avg Health Score",     f"{avg_h:.1f}", "out of 100")
c2.metric("Active Accounts",      f"{len(health):,}")
c3.metric("Champion Tier",        f"{champion_n}", f"${champion_mrr:,.0f} MRR")
c4.metric("High + Critical Risk", f"{at_risk_n}",
          f"${at_risk_mrr:,.0f} MRR at risk" if at_risk_n > 0 else "no accounts in high risk")
c5.metric("Median Health Score",  f"{health['health_score'].median():.1f}", "50th percentile")

st.divider()

# ── Health score distribution + risk pie ──────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Health Score Distribution")
    st.caption("Histogram of composite health scores across all active accounts.")
    fig_hist = go.Figure(go.Histogram(
        x=health["health_score"], nbinsx=20,
        marker_color=C["accent"], marker_line_width=0, opacity=0.8,
        hovertemplate="Score %{x}–%{x}: %{y} customers<extra></extra>",
    ))
    for boundary, tier_color, label in [
        (30, C["red"],   "Critical"), (50, C["amber"], "High"),
        (70, "#D97706",  "Medium"),   (85, C["green"],  "Low"),
    ]:
        fig_hist.add_vline(x=boundary, line_dash="dot", line_color=tier_color, line_width=1.5,
                           opacity=0.6,
                           annotation_text=label, annotation_font_size=9,
                           annotation_font_color=tier_color, annotation_position="top")
    fig_hist.add_vline(x=avg_h, line_color=C["text"], line_width=2, opacity=0.5,
                       annotation_text=f"avg {avg_h:.1f}",
                       annotation_font_size=10, annotation_position="top right")
    lay = chart_layout(height=320)
    lay.update({"xaxis": {**lay.get("xaxis", {}),
                           "title": dict(text="Health score", font=dict(size=11, color=C["text_muted"]))},
                "yaxis": {**lay.get("yaxis", {}),
                           "title": dict(text="Accounts", font=dict(size=11, color=C["text_muted"]))}})
    fig_hist.update_layout(**lay)
    st.plotly_chart(fig_hist, use_container_width=True)

with col_r:
    st.subheader("Risk Tier Distribution")
    st.caption("MRR share by risk tier — size of the wedge reflects revenue concentration.")
    tier_df_plot = tier_counts.reset_index()
    tier_df_plot["label"] = tier_df_plot["risk_tier"].map(TIER_LABELS)
    fig_pie = go.Figure(go.Pie(
        labels=tier_df_plot["label"],
        values=tier_df_plot["mrr"],
        hole=0.55,
        marker=dict(
            colors=[TIER_COLORS.get(t, C["accent"]) for t in tier_df_plot["risk_tier"]],
            line=dict(color="white", width=2),
        ),
        hovertemplate="%{label}<br>MRR: $%{value:,.0f}<br>%{percent}<extra></extra>",
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig_pie.update_layout(
        paper_bgcolor="white", height=320,
        margin=dict(t=12, b=24, l=12, r=12),
        showlegend=False,
        font=dict(family="sans-serif", color=C["text_muted"]),
        annotations=[dict(text=f"${risk['mrr_usd'].sum():,.0f}<br>total MRR",
                          x=0.5, y=0.5, font_size=12, showarrow=False,
                          font_color=C["text"])],
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Health score vs MRR scatter ───────────────────────────────────────────────
st.subheader("Health Score vs MRR")
st.caption("Each dot is one active account. Size = MRR. Accounts in the lower-left need immediate attention.")

scatter_df = health.merge(risk[["customer_id", "risk_tier"]], on="customer_id")

fig_scatter = go.Figure()
for tier in TIER_ORDER:
    sub = scatter_df[scatter_df["risk_tier"] == tier]
    if sub.empty:
        continue
    fig_scatter.add_trace(go.Scatter(
        x=sub["health_score"], y=sub["mrr_usd"],
        mode="markers",
        name=TIER_LABELS[tier],
        marker=dict(
            color=TIER_COLORS[tier], size=sub["mrr_usd"].clip(upper=2000) / 80 + 4,
            opacity=0.65, line=dict(width=0.5, color="white"),
        ),
        customdata=sub[["company_name", "plan_name", "tenure_months"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Health: %{x:.1f} · MRR: $%{y:,.0f}<br>"
            "Plan: %{customdata[1]} · Tenure: %{customdata[2]}m<extra></extra>"
        ),
    ))

for boundary, color, label in [
    (30, C["red"],  "Critical"), (50, C["amber"], "High risk"),
    (70, "#D97706", "Medium"),   (85, C["green"],  "Low risk"),
]:
    fig_scatter.add_vline(x=boundary, line_dash="dot", line_color=color,
                          line_width=1, opacity=0.35,
                          annotation_text=label, annotation_font_size=9,
                          annotation_font_color=color, annotation_position="top")

lay2 = chart_layout(height=400)
lay2.update({
    "showlegend": True,
    "xaxis": {**lay2.get("xaxis", {}),
              "title": dict(text="Health score", font=dict(size=11, color=C["text_muted"])),
              "range": [0, 105]},
    "yaxis": {**lay2.get("yaxis", {}),
              "title": dict(text="MRR ($)", font=dict(size=11, color=C["text_muted"])),
              "tickprefix": "$", "tickformat": ",.0f"},
})
fig_scatter.update_layout(**lay2)
st.plotly_chart(fig_scatter, use_container_width=True)

st.info("Accounts in the **lower-left quadrant** (low health, high MRR) represent "
        "the highest business risk — significant revenue with leading churn indicators. "
        "Champion-tier accounts (upper-right) are upsell and referral candidates.")

# ── Individual account drill-down ─────────────────────────────────────────────
st.divider()
st.subheader("Account Deep Dive")
st.caption("Select a customer to view their component score breakdown.")

col_pick, col_radar = st.columns([1, 2])

with col_pick:
    seg_opt  = st.selectbox("Segment",   ["All"] + sorted(health["segment"].unique().tolist()))
    tier_opt = st.selectbox("Risk tier", ["All"] + TIER_ORDER)

    filt = risk.copy()
    if seg_opt  != "All": filt = filt[filt["segment"]   == seg_opt]
    if tier_opt != "All": filt = filt[filt["risk_tier"] == tier_opt]

    names = filt.sort_values("health_score")["company_name"].tolist()
    if names:
        sel_name = st.selectbox("Account", names)
        row  = health[health["company_name"] == sel_name].iloc[0]
        rrow = risk[risk["company_name"]     == sel_name].iloc[0]

        tier_color = TIER_COLORS.get(rrow.risk_tier, C["accent"])
        st.markdown(f"**{sel_name}**")
        st.markdown(f"{row.plan_name} · {row.billing_interval} · {int(row.tenure_months)}m tenure")
        st.markdown(f"Health: **{row.health_score:.1f}** &nbsp; "
                    f"<span style='color:{tier_color}'>{rrow.risk_tier.upper()}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"MRR: **${row.mrr_usd:,.2f}** / month")
        st.info(rrow.recommended_action)
    else:
        st.info("No accounts match the selected filters.")

with col_radar:
    if names:
        cats  = ["Usage", "Payment", "Support", "Tenure", "Features"]
        vals  = [row.usage_score, row.payment_score, row.support_score,
                 row.tenure_score, row.feature_score]
        avg_v = [health["usage_score"].mean(), health["payment_score"].mean(),
                 health["support_score"].mean(), health["tenure_score"].mean(),
                 health["feature_score"].mean()]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_v + [avg_v[0]], theta=cats + [cats[0]],
            fill="toself", name="Avg customer",
            line_color=C["border"], fillcolor="rgba(226,232,240,0.4)",
            opacity=0.8,
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=sel_name,
            line_color=C["accent"], fillcolor="rgba(37,99,235,0.15)",
            opacity=0.9,
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="white",
                radialaxis=dict(range=[0, 100], showticklabels=True,
                                tickfont=dict(size=9, color=C["text_faint"]),
                                gridcolor=C["border"], linecolor=C["border"]),
                angularaxis=dict(tickfont=dict(size=12, color=C["text_muted"]),
                                 gridcolor=C["border"], linecolor=C["border"]),
            ),
            showlegend=True,
            height=380,
            margin=dict(t=40, b=20, l=40, r=40),
            paper_bgcolor="white",
            font=dict(family="sans-serif", color=C["text_muted"], size=12),
            legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)",
                        orientation="h", y=-0.1),
            title=dict(text=f"Score breakdown — {sel_name}",
                       font=dict(size=13, color=C["text"]), x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ── At-risk accounts table ────────────────────────────────────────────────────
st.divider()
at_risk_df = risk[risk["risk_tier"].isin(["critical", "high"])].copy()

st.subheader(f"High & Critical Risk Accounts")
st.caption(f"{len(at_risk_df)} account{'s' if len(at_risk_df) != 1 else ''} requiring immediate attention — "
           f"${at_risk_mrr:,.0f} in combined MRR.")

if at_risk_df.empty:
    st.success("No accounts are currently in the critical or high risk tier.")
else:
    def fmt_flags(row):
        f = []
        if row.flag_usage_declining:      f.append("Usage ↓")
        if row.flag_payment_issues:       f.append("Payment")
        if row.flag_support_overloaded:   f.append("Support")
        if row.flag_low_feature_adoption: f.append("Low adopt")
        if row.flag_new_customer_risk:    f.append("New acct")
        return ", ".join(f) if f else "—"

    at_risk_df["Risk Flags"] = at_risk_df.apply(fmt_flags, axis=1)
    st.dataframe(
        at_risk_df[[
            "company_name", "segment", "plan_name", "mrr_usd", "health_score",
            "risk_tier", "Risk Flags", "recommended_action"
        ]].rename(columns={
            "company_name":       "Company",
            "segment":            "Segment",
            "plan_name":          "Plan",
            "mrr_usd":            "MRR ($)",
            "health_score":       "Health",
            "risk_tier":          "Tier",
            "recommended_action": "Action",
        })
        .style.format({"MRR ($)": "${:,.2f}", "Health": "{:.1f}"}),
        use_container_width=True, hide_index=True,
    )
