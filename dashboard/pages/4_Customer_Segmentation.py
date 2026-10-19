"""
Customer Segmentation & RFM Clustering — Smart Retail Analytics
Unsupervised machine learning customer profiling, silhouette validation, and strategic playbooks.
"""

import sys
import os

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.data_loader import (
    load_customer_segments,
    load_clustering_validation,
)
from components.metrics import format_currency, format_number, format_pct
from components.charts import (
    plot_customer_scatter_2d,
    plot_customer_scatter_3d,
    plot_elbow_and_silhouette,
)
from components.insights import render_segment_playbook, render_footer

st.set_page_config(page_title="Customer Segmentation | Smart Retail", page_icon="🎯", layout="wide")

st.title("🎯 Customer Segmentation & RFM Intelligence")
st.markdown("Machine learning customer profiling using Recency, Frequency, and Monetary (RFM) clustering.")

try:
    df_segments = load_customer_segments()
    val_data = load_clustering_validation()
except Exception as e:
    st.error(f"Failed to load customer segmentation data: {e}. Please run 'python customer_segmentation.py' first.")
    st.stop()

# ──────────────────────────────────────────────
# HIGH-LEVEL SEGMENTATION METRICS
# ──────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Customers Segmented", format_number(len(df_segments)), help="Unique CustomerIDs processed through RFM pipeline")
with m2:
    st.metric("Selected Clusters (K)", str(val_data.get("selected_k", 4)), help="Optimal cluster count balancing statistical separation and business utility")
with m3:
    st.metric("Silhouette Score (K=4)", f"{val_data.get('selected_k_silhouette', 0.6162):.4f}", help="Cluster cohesion and separation coefficient (-1 to +1)")
with m4:
    st.metric("Largest Segment", f"{df_segments['Segment'].value_counts().index[0]} ({df_segments['Segment'].value_counts().iloc[0]:,})")

st.markdown("---")

# ──────────────────────────────────────────────
# SEGMENT METHODOLOGY TOGGLE
# ──────────────────────────────────────────────
st.subheader("1. Segment Distribution & Profile Analysis")

methodology = st.radio(
    "Select Segmentation Methodology:",
    options=["K-Means Clustering (Unsupervised ML)", "RFM Quintile Score Segmentation (Rules-Based)"],
    horizontal=True,
    help="K-Means groups customers mathematically in 3D scaled space. RFM Score divides R, F, and M into 1-5 quintiles."
)

if methodology == "K-Means Clustering (Unsupervised ML)":
    segment_col = "Segment"
    st.caption("K-Means groups accounts into 4 clusters based on Euclidean proximity in standardized RFM space.")
else:
    segment_col = "RFM_Segment"
    st.caption("RFM Score groups customers based on independent 1-5 quintile scores: Champions (12-15), Potential Loyalists (9-11), Needs Attention (6-8), At Risk (3-5).")

seg_summary = df_segments.groupby(segment_col).agg(
    CustomerCount   = ("CustomerID", "count"),
    Recency_Mean    = ("Recency",    "mean"),
    Recency_Median  = ("Recency",    "median"),
    Frequency_Mean  = ("Frequency",  "mean"),
    Frequency_Median= ("Frequency",  "median"),
    Monetary_Mean   = ("Monetary",   "mean"),
    Monetary_Median = ("Monetary",   "median")
).reset_index()

seg_summary["PopulationPct"] = (seg_summary["CustomerCount"] / len(df_segments) * 100).round(1)

col_s1, col_s2 = st.columns([1, 2])
with col_s1:
    st.bar_chart(seg_summary, x=segment_col, y="CustomerCount", color="#1E88E5", use_container_width=True)

with col_s2:
    st.dataframe(
        seg_summary.style.format({
            "CustomerCount": "{:,}",
            "PopulationPct": "{:.1f}%",
            "Recency_Mean": "{:.1f}d",
            "Recency_Median": "{:.1f}d",
            "Frequency_Mean": "{:.1f}",
            "Frequency_Median": "{:.1f}",
            "Monetary_Mean": "£{:,.2f}",
            "Monetary_Median": "£{:,.2f}"
        }),
        use_container_width=True
    )

st.markdown("---")

# ──────────────────────────────────────────────
# INTERACTIVE 2D & 3D CLUSTER SPACES
# ──────────────────────────────────────────────
st.subheader("2. Interactive Customer Scatter Visualizations")

tab_2d, tab_3d = st.tabs(["2D RFM Scatter Spaces", "3D Interactive Space"])

with tab_2d:
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        fig_fm = plot_customer_scatter_2d(
            df_segments,
            x_col="Frequency",
            y_col="Monetary",
            color_col=segment_col,
            log_x=True,
            log_y=True
        )
        st.plotly_chart(fig_fm, use_container_width=True)
    with col_sc2:
        fig_rm = plot_customer_scatter_2d(
            df_segments,
            x_col="Recency",
            y_col="Monetary",
            color_col=segment_col,
            log_x=False,
            log_y=True
        )
        st.plotly_chart(fig_rm, use_container_width=True)

with tab_3d:
    st.caption("Rotate, pan, and zoom to inspect cluster boundaries in 3D RFM coordinates (showing sample of 2,000 customers for smooth rendering):")
    fig_3d = plot_customer_scatter_3d(df_segments)
    st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# CLUSTERING VALIDATION & RATIONALE
# ──────────────────────────────────────────────
st.subheader("3. Model Validation & K Selection Rationale")

val_col1, val_col2 = st.columns([3, 2])
with val_col1:
    tested_k = val_data.get("tested_k", [])
    if tested_k:
        fig_eval = plot_elbow_and_silhouette(tested_k, selected_k=val_data.get("selected_k", 4))
        st.plotly_chart(fig_eval, use_container_width=True)

with val_col2:
    st.markdown("#### ⚖️ Mathematical vs Business Trade-Off")
    st.info(val_data.get("selection_rationale", ""))
    
    with st.expander("View Full K Evaluation Metrics"):
        st.dataframe(pd.DataFrame(tested_k).style.format({
            "inertia": "{:,.2f}",
            "silhouette": "{:.4f}"
        }), use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# STRATEGIC MARKETING PLAYBOOKS
# ──────────────────────────────────────────────
st.subheader("4. Actionable Segment Marketing Playbooks")
st.caption("Prescriptive business actions, objectives, and monitoring KPIs for each validated customer segment:")
render_segment_playbook()

st.markdown("---")

# ──────────────────────────────────────────────
# CUSTOMER EXPLORER TABLE
# ──────────────────────────────────────────────
st.subheader("5. Customer Segment Explorer")
c_filter1, c_filter2 = st.columns([1, 2])
with c_filter1:
    seg_filter = st.selectbox("Filter by Segment:", options=["All"] + df_segments["Segment"].unique().tolist())
with c_filter2:
    cust_search = st.text_input("Search CustomerID:", placeholder="e.g. 12346, 17850")

df_display = df_segments.copy()
if seg_filter != "All":
    df_display = df_display[df_display["Segment"] == seg_filter]
if cust_search.strip():
    df_display = df_display[df_display["CustomerID"].astype(str).str.contains(cust_search.strip())]

st.write(f"Showing **{len(df_display):,}** customers:")
st.dataframe(
    df_display[["CustomerID", "Recency", "Frequency", "Monetary", "Segment", "RFM_Score", "RFM_Segment"]]
    .style.format({
        "Recency": "{:,.0f} days",
        "Frequency": "{:,.0f} orders",
        "Monetary": "£{:,.2f}",
        "CustomerID": "{}"
    }),
    use_container_width=True
)

render_footer()
