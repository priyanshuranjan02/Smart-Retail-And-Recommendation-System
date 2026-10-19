"""
Smart Retail Analytics Dashboard — Metrics & KPI Component
Provides standardized formatting and rich UI KPI card renderers.
"""

import streamlit as st
from typing import Optional, Union


def format_currency(val: Union[int, float], compact: bool = False) -> str:
    """Format numeric value as British Pounds (£)."""
    if val is None or pd_is_nan(val):
        return "£0.00"
    if compact:
        if abs(val) >= 1_000_000:
            return f"£{val / 1_000_000:.2f}M"
        if abs(val) >= 1_000:
            return f"£{val / 1_000:.1f}K"
    return f"£{val:,.2f}"


def format_number(val: Union[int, float]) -> str:
    """Format integer or float with thousand commas."""
    if val is None or pd_is_nan(val):
        return "0"
    return f"{int(val):,}"


def format_pct(val: Union[int, float]) -> str:
    """Format decimal or percentage value."""
    if val is None or pd_is_nan(val):
        return "0.0%"
    return f"{val:+.2f}%" if val != 0 else "0.0%"


def pd_is_nan(val: Any) -> bool:
    try:
        import math
        return math.isnan(val)
    except Exception:
        return False


def render_kpi_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    subtext: Optional[str] = None,
    help_text: Optional[str] = None
):
    """Render a polished, responsive KPI metric card in Streamlit."""
    delta_color = "normal"
    if delta:
        if delta.startswith("+"):
            delta_color = "normal"
        elif delta.startswith("-"):
            delta_color = "inverse"

    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text,
    )
    if subtext:
        st.caption(subtext)


def render_segment_badge(segment_name: str) -> str:
    """Return an HTML badge with consistent segment color."""
    colors = {
        "Champions (High-Value)": "#2E7D32",    # Deep Green
        "Champions": "#2E7D32",
        "Loyal Customers": "#1976D2",           # Blue
        "Potential Loyalists": "#0288D1",       # Light Blue
        "Regular Customers": "#F57C00",         # Orange
        "Needs Attention": "#FFA000",           # Amber
        "At-Risk (Low-Value)": "#D32F2F",       # Red
        "At Risk / Lost": "#C2185B",            # Deep Rose
    }
    bg = colors.get(segment_name, "#546E7A")
    return f"""<span style="background-color: {bg}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.82rem;">{segment_name}</span>"""
