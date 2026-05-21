"""Cohort Retention — monthly cohort triangle heatmap and average curve."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from db import query
from style import C, chart_layout

st.set_page_config(page_title="Cohort Retention", page_icon="🔁", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────────
df = query("""
    SELECT cohort_month, cohort_size, period_number, retention_pct
    FROM analytics.cohort_retention
    ORDER BY cohort_month, period_number
""")
df["cohort_month"] = df["cohort_month"].astype(str)

max_period = int(df["period_number"].max())

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Cohort Retention")
st.caption("What percentage of each monthly cohort is still active at 1, 3, 6, and 12 months? "
           "Period 0 = cohort's first month (always 100%).")
st.divider()

# ── Period selector ───────────────────────────────────────────────────────────
col_ctrl, _ = st.columns([2, 3])
with col_ctrl:
    max_p = st.slider("Show periods up to month", 3, max_period,
                      min(12, max_period), label_visibility="visible")

dff = df[df["period_number"] <= max_p]
pivot = dff.pivot(index="cohort_month", columns="period_number", values="retention_pct")

# ── KPI row ───────────────────────────────────────────────────────────────────
avg_m3  = df[df["period_number"] == 3]["retention_pct"].mean()
avg_m6  = df[df["period_number"] == 6]["retention_pct"].mean()
avg_m12 = df[df["period_number"] == 12]["retention_pct"].mean() if max_period >= 12 else None
cohort_sizes = df[df["period_number"] == 0][["cohort_month", "cohort_size"]]
total_cohorts = len(cohort_sizes)
avg_size = cohort_sizes["cohort_size"].mean()

cols_kpi = st.columns(5 if avg_m12 is not None else 4)
cols_kpi[0].metric("Total Cohorts",    f"{total_cohorts}")
cols_kpi[1].metric("Avg Cohort Size",  f"{avg_size:.0f}")
cols_kpi[2].metric("Avg M3 Retention", f"{avg_m3:.1f}%")
cols_kpi[3].metric("Avg M6 Retention", f"{avg_m6:.1f}%")
if avg_m12 is not None and len(cols_kpi) > 4:
    cols_kpi[4].metric("Avg M12 Retention", f"{avg_m12:.1f}%")

st.divider()

# ── Retention heatmap ─────────────────────────────────────────────────────────
st.subheader("Cohort Retention Triangle")
st.caption("Each cell shows % of the original cohort still active. "
           "Blank = future months not yet observable.")

z_vals    = pivot.values.tolist()
x_lbls    = [f"M{p}" for p in pivot.columns.tolist()]
y_lbls    = pivot.index.tolist()
text_vals = [
    [f"{v:.0f}%" if v is not None and not pd.isna(v) else "" for v in row]
    for row in z_vals
]

colorscale = [
    [0.00, "#EFF6FF"],
    [0.40, "#93C5FD"],
    [0.70, "#3B82F6"],
    [1.00, "#1E40AF"],
]

fig_heat = go.Figure(go.Heatmap(
    z=z_vals, x=x_lbls, y=y_lbls,
    colorscale=colorscale,
    zmin=0, zmax=100,
    text=text_vals,
    texttemplate="%{text}",
    textfont={"size": 10, "color": C["text"]},
    hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
    colorbar=dict(
        title=dict(text="Retention %", font=dict(size=11, color=C["text_muted"])),
        ticksuffix="%",
        tickfont=dict(size=10, color=C["text_muted"]),
        thickness=12, len=0.85,
    ),
))
fig_heat.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="sans-serif", color=C["text_muted"], size=11),
    height=max(380, 28 * len(y_lbls) + 100),
    margin=dict(t=12, b=60, l=80, r=40),
    xaxis=dict(side="bottom", tickfont=dict(size=11, color=C["text_muted"]),
               showgrid=False, zeroline=False),
    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color=C["text_muted"]),
               showgrid=False, zeroline=False),
)
st.plotly_chart(fig_heat, use_container_width=True)

st.info(f"Cohort retention stabilises significantly after month 6. "
        f"Average M3 retention of **{avg_m3:.1f}%** indicates strong early-stage product stickiness. "
        f"The M3→M6 drop-off is the highest-leverage window for customer success intervention.")

# ── Average retention curve + cohort sizes ────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Average Retention Curve")
    st.caption("Mean retention across all cohorts at each period.")
    avg_curve = df.groupby("period_number")["retention_pct"].mean().reset_index()
    avg_curve = avg_curve[avg_curve["period_number"] <= max_p]

    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=avg_curve["period_number"], y=avg_curve["retention_pct"],
        mode="lines+markers",
        line=dict(color=C["accent"], width=2.5),
        marker=dict(size=5, color=C["accent"]),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
        hovertemplate="Month %{x}: %{y:.1f}%<extra></extra>",
    ))
    lay = chart_layout(height=320)
    lay.update({
        "xaxis": {**lay.get("xaxis", {}),
                  "title": dict(text="Months since first subscription",
                                font=dict(size=11, color=C["text_muted"])),
                  "dtick": 1},
        "yaxis": {**lay.get("yaxis", {}),
                  "ticksuffix": "%", "range": [0, 105],
                  "title": dict(text="Avg retention",
                                font=dict(size=11, color=C["text_muted"]))},
    })
    fig_curve.update_layout(**lay)
    st.plotly_chart(fig_curve, use_container_width=True)

with col_r:
    st.subheader("Cohort Sizes")
    st.caption("Number of customers acquired per cohort month.")
    fig_size = go.Figure(go.Bar(
        x=cohort_sizes["cohort_month"], y=cohort_sizes["cohort_size"],
        marker_color=C["accent"], marker_line_width=0, opacity=0.8,
        hovertemplate="%{y} customers<extra>%{x}</extra>",
    ))
    fig_size.add_hline(y=avg_size, line_dash="dot", line_color=C["amber"], line_width=1.5,
                       annotation_text=f"avg {avg_size:.0f}",
                       annotation_font_size=10, annotation_font_color=C["amber"],
                       annotation_position="top right")
    lay2 = chart_layout(height=320)
    lay2.update({"yaxis": {**lay2.get("yaxis", {}),
                            "title": dict(text="Customers",
                                          font=dict(size=11, color=C["text_muted"]))}})
    fig_size.update_layout(**lay2)
    st.plotly_chart(fig_size, use_container_width=True)

# ── Single-period snapshot ─────────────────────────────────────────────────────
st.divider()
st.subheader("Retention Snapshot at Selected Period")
st.caption("Compare retention across all cohorts at a single point in time.")

sel = st.slider("Period (months after first subscription)", 0, max_p, 6)
snap = df[df["period_number"] == sel].sort_values("cohort_month")
if not snap.empty:
    avg_snap = snap["retention_pct"].mean()
    colors = [C["green"] if v >= 80 else C["amber"] if v >= 60 else C["red"]
              for v in snap["retention_pct"]]
    fig_snap = go.Figure(go.Bar(
        x=snap["cohort_month"], y=snap["retention_pct"],
        marker_color=colors, marker_line_width=0, opacity=0.85,
        hovertemplate="%{y:.1f}%<extra>%{x}</extra>",
    ))
    fig_snap.add_hline(y=avg_snap, line_dash="dot", line_color=C["text_muted"], line_width=1.5,
                       annotation_text=f"avg {avg_snap:.1f}%",
                       annotation_font_size=10, annotation_font_color=C["text_muted"],
                       annotation_position="bottom right")
    lay3 = chart_layout(height=260)
    lay3.update({"yaxis": {**lay3.get("yaxis", {}), "ticksuffix": "%", "range": [0, 105]}})
    fig_snap.update_layout(**lay3)
    st.plotly_chart(fig_snap, use_container_width=True)
