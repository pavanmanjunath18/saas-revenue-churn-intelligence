"""Color tokens and lightweight helpers — no CSS injection."""

# ── Color tokens ──────────────────────────────────────────────────────────────
C = {
    "bg":           "#F8FAFC",
    "card":         "#FFFFFF",
    "text":         "#0F172A",
    "text_muted":   "#64748B",
    "text_faint":   "#94A3B8",
    "border":       "#E2E8F0",
    "border_light": "#F1F5F9",
    "accent":       "#2563EB",
    "green":        "#16A34A",
    "red":          "#DC2626",
    "amber":        "#D97706",
    "violet":       "#7C3AED",
    "cyan":         "#0891B2",
}

SEGMENT_COLORS = {
    "smb":        "#60A5FA",
    "mid_market": "#34D399",
    "enterprise": "#A78BFA",
}

CHART_COLORS = [
    C["accent"], C["green"], C["red"], C["amber"], C["violet"],
]


def chart_layout(height: int = 320, **kwargs) -> dict:
    """Return a Plotly layout dict with clean styling."""
    base = dict(
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        font=dict(family="sans-serif", color=C["text_muted"], size=12),
        height=height,
        margin=dict(t=20, b=44, l=0, r=8),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=C["text"], font_color="white",
            font_size=12, bordercolor=C["text"],
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=11, color=C["text_muted"]),
            linecolor=C["border"],
        ),
        yaxis=dict(
            showgrid=True, gridcolor=C["border"], gridwidth=1,
            zeroline=False,
            tickfont=dict(size=11, color=C["text_muted"]),
            linecolor="rgba(0,0,0,0)",
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(size=12, color=C["text_muted"]),
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        showlegend=False,
    )
    base.update(kwargs)
    return base
