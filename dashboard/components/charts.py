"""
Smart Retail Analytics Dashboard — Plotly Interactive Visualization Library
Provides consistent visual themes, legends, tooltips, and responsive layouts.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

# Standard Palette
THEME_COLORS = {
    "primary": "#1E88E5",
    "secondary": "#26A69A",
    "accent": "#FFA726",
    "danger": "#EF5350",
    "dark": "#263238",
    "light": "#ECEFF1"
}

SEGMENT_COLORS = {
    "Champions (High-Value)": "#2E7D32",
    "Loyal Customers": "#1976D2",
    "Regular Customers": "#F57C00",
    "At-Risk (Low-Value)": "#D32F2F",
    "Champions": "#2E7D32",
    "Potential Loyalists": "#0288D1",
    "Needs Attention": "#FFA000",
    "At Risk / Lost": "#C2185B"
}


def apply_standard_layout(fig: go.Figure, title: str, x_title: Optional[str] = None, y_title: Optional[str] = None) -> go.Figure:
    """Apply consistent typography, margin, hover, and grid styling."""
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16)),
        xaxis=dict(title=x_title, showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        yaxis=dict(title=y_title, showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_monthly_revenue_and_growth(df: pd.DataFrame) -> go.Figure:
    """Dual-axis chart displaying monthly revenue bars and MoM growth line."""
    fig = go.Figure()

    # Revenue Bars
    fig.add_trace(go.Bar(
        x=df["YearMonth"],
        y=df["TotalRevenue"],
        name="Gross Revenue (£)",
        marker_color="#1E88E5",
        hovertemplate="Revenue: £%{y:,.2f}<extra></extra>"
    ))

    # AOV Line
    if "AvgOrderValue" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["YearMonth"],
            y=df["AvgOrderValue"],
            name="Avg Order Value (£)",
            yaxis="y2",
            mode="lines+markers",
            marker=dict(size=6, color="#FFA726"),
            line=dict(width=2, dash="dot"),
            hovertemplate="AOV: £%{y:,.2f}<extra></extra>"
        ))

    fig.update_layout(
        title=dict(text="<b>Monthly Revenue Trends & Average Order Value</b>", font=dict(size=16)),
        xaxis=dict(title="Month (Year-MM)", tickangle=-45),
        yaxis=dict(title="Gross Revenue (£)", showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        yaxis2=dict(
            title="Avg Order Value (£)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_mom_growth(df_growth: pd.DataFrame) -> go.Figure:
    """Waterfall/Bar chart of Month-over-Month growth rate (%)."""
    colors = ["#2E7D32" if g >= 0 else "#D32F2F" for g in df_growth["GrowthPct"]]
    fig = go.Figure(go.Bar(
        x=df_growth["YearMonth"],
        y=df_growth["GrowthPct"],
        marker_color=colors,
        text=[f"{v:+.1f}%" if pd.notnull(v) else "" for v in df_growth["GrowthPct"]],
        textposition="outside",
        hovertemplate="Growth: %{y:+.2f}%<extra></extra>"
    ))
    return apply_standard_layout(fig, "Month-over-Month (MoM) Revenue Growth Rate (%)", "Month", "Growth (%)")


def plot_sales_volume_trends(df: pd.DataFrame) -> go.Figure:
    """Line chart comparing units sold vs number of orders by month."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["YearMonth"],
        y=df["TotalOrders"],
        name="Orders Placed",
        mode="lines+markers",
        line=dict(color="#1976D2", width=2.5),
        hovertemplate="Orders: %{y:,}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df["YearMonth"],
        y=df["TotalUnitsSold"],
        name="Units Sold",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#26A69A", width=2.5),
        hovertemplate="Units: %{y:,}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Order Volume & Units Sold Trends</b>", font=dict(size=16)),
        xaxis=dict(title="Month (Year-MM)", tickangle=-45),
        yaxis=dict(title="Total Orders", showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        yaxis2=dict(title="Total Units Sold", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_top_countries(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart showing top revenue generating countries."""
    df_plot = df.head(top_n).sort_values("TotalRevenue", ascending=True)
    fig = go.Figure(go.Bar(
        x=df_plot["TotalRevenue"],
        y=df_plot["Country"],
        orientation="h",
        marker_color="#1E88E5",
        text=[f"£{v/1000:,.1f}K ({s:.1f}%)" if v < 1_000_000 else f"£{v/1_000_000:,.2f}M ({s:.1f}%)" 
              for v, s in zip(df_plot["TotalRevenue"], df_plot["RevenueSharePct"])],
        textposition="auto",
        hovertemplate="Country: %{y}<br>Revenue: £%{x:,.2f}<extra></extra>"
    ))
    return apply_standard_layout(fig, f"Top {top_n} Countries by Revenue & Market Share", "Revenue (£)", "Country")


def plot_top_products(df: pd.DataFrame, metric: str = "TotalRevenue", title: str = "Top Products") -> go.Figure:
    """Horizontal bar chart for top products."""
    df_sorted = df.sort_values(metric, ascending=True)
    # Truncate long descriptions for clean axes
    clean_desc = [d[:35] + "..." if len(d) > 35 else d for d in df_sorted["Description"]]
    fig = go.Figure(go.Bar(
        x=df_sorted[metric],
        y=clean_desc,
        orientation="h",
        marker_color="#26A69A",
        hovertemplate="Product: %{y}<br>Value: %{x:,.2f}<extra></extra>"
    ))
    return apply_standard_layout(fig, title, metric, "Product")


def plot_retention_pie(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing customer retention distribution."""
    fig = go.Figure(go.Pie(
        labels=df["CustomerType"],
        values=df["CustomerCount"],
        hole=0.45,
        marker=dict(colors=["#1E88E5", "#FFA726", "#2E7D32"]),
        hovertemplate="Segment: %{label}<br>Customers: %{value:,} (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Customer Retention & Purchase Frequency Mix</b>", font=dict(size=16)),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_day_of_week(df: pd.DataFrame) -> go.Figure:
    """Bar chart of sales aggregated by day of the week."""
    fig = go.Figure(go.Bar(
        x=df["DayName"],
        y=df["Revenue"],
        marker_color="#3949AB",
        text=[f"£{v/1000:,.1f}K" for v in df["Revenue"]],
        textposition="outside",
        hovertemplate="Day: %{x}<br>Revenue: £%{y:,.2f}<extra></extra>"
    ))
    return apply_standard_layout(fig, "Revenue by Day of Week", "Day", "Revenue (£)")


def plot_region_share(df: pd.DataFrame) -> go.Figure:
    """Donut chart for continental region revenue share."""
    fig = go.Figure(go.Pie(
        labels=df["Region"],
        values=df["Revenue"],
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Prism),
        hovertemplate="Region: %{label}<br>Revenue: £%{value:,.2f} (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="<b>Continental Regional Revenue Share</b>", font=dict(size=16)),
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_customer_scatter_2d(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = "Segment",
    log_x: bool = False,
    log_y: bool = False
) -> go.Figure:
    """Interactive 2D scatter plot with custom cluster colors and hover tooltips."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        color_discrete_map=SEGMENT_COLORS,
        log_x=log_x,
        log_y=log_y,
        hover_data=["CustomerID", "Recency", "Frequency", "Monetary"],
        title=f"<b>Customer Clusters: {x_col} vs {y_col}</b>",
        opacity=0.65
    )
    fig.update_traces(marker=dict(size=6, line=dict(width=0.5, color="white")))
    fig.update_layout(
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_customer_scatter_3d(df: pd.DataFrame, sample_size: int = 2000) -> go.Figure:
    """Interactive 3D scatter plot of Recency, Frequency, and Monetary space."""
    df_sampled = df.sample(n=min(len(df), sample_size), random_state=42) if len(df) > sample_size else df
    fig = px.scatter_3d(
        df_sampled,
        x="Recency",
        y="Frequency",
        z="Monetary",
        color="Segment",
        color_discrete_map=SEGMENT_COLORS,
        hover_data=["CustomerID", "Recency", "Frequency", "Monetary"],
        opacity=0.7,
        title="<b>3D Customer Segmentation Space (RFM)</b>"
    )
    fig.update_traces(marker=dict(size=3.5))
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis_title="Recency (days)",
            yaxis_title="Frequency (orders)",
            zaxis_title="Monetary (£)"
        )
    )
    return fig


def plot_elbow_and_silhouette(tested_k_list: list[dict], selected_k: int = 4) -> go.Figure:
    """Two-panel chart showing Elbow Inertia and Silhouette scores across K."""
    k_vals = [item["k"] for item in tested_k_list]
    inertias = [item["inertia"] for item in tested_k_list]
    silhouettes = [item["silhouette"] for item in tested_k_list]

    fig = go.Figure()

    # Inertia trace
    fig.add_trace(go.Scatter(
        x=k_vals,
        y=inertias,
        mode="lines+markers",
        name="Inertia (Within-Cluster SS)",
        marker=dict(color="#1976D2", size=8),
        line=dict(width=2),
        hovertemplate="K=%{x}<br>Inertia=%{y:,.2f}<extra></extra>"
    ))

    # Silhouette trace on secondary y-axis
    fig.add_trace(go.Scatter(
        x=k_vals,
        y=silhouettes,
        mode="lines+markers",
        name="Silhouette Score",
        yaxis="y2",
        marker=dict(color="#D32F2F", size=8, symbol="square"),
        line=dict(width=2, dash="dash"),
        hovertemplate="K=%{x}<br>Silhouette=%{y:.4f}<extra></extra>"
    ))

    # Add vertical line for selected K
    fig.add_vline(x=selected_k, line_width=2, line_dash="dot", line_color="green",
                  annotation_text=f"Selected K={selected_k}", annotation_position="top left")

    fig.update_layout(
        title=dict(text="<b>Cluster Validation: Elbow Method & Silhouette Score Progression</b>", font=dict(size=16)),
        xaxis=dict(title="Number of Clusters (K)", dtick=1),
        yaxis=dict(title="Inertia", showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        yaxis2=dict(title="Silhouette Score", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_rules_scatter(df_rules: pd.DataFrame) -> go.Figure:
    """Scatter plot of Support vs Confidence colored and sized by Lift."""
    fig = px.scatter(
        df_rules,
        x="support",
        y="confidence",
        size="lift",
        color="lift",
        color_continuous_scale="Viridis",
        hover_data=["antecedents", "consequents", "support", "confidence", "lift"],
        title="<b>Association Rules Landscape: Support vs Confidence (Sized by Lift)</b>",
        labels={"support": "Support (Transaction Prevalence)", "confidence": "Confidence (P(B|A))", "lift": "Lift Factor"}
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
