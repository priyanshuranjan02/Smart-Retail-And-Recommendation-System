"""
Smart Retail Analytics & Recommendation Warehouse — Main Application Portal
Interactive E-commerce Customer Intelligence System.
"""

import os
import sys

# Ensure repository root and dashboard dir are on sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from components.data_loader import (
    check_artifact_status,
    load_kpis,
    ensure_warehouse_database,
)
from components.metrics import format_currency, format_number
from components.insights import render_footer

st.set_page_config(
    page_title="Smart Retail Analytics & Recommendation Warehouse",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished interface
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1565C0;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #546E7A;
        margin-bottom: 1.5rem;
    }
    .card-container {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 1.2rem;
        border: 1px solid #E0E0E0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=64)
    st.title("Smart Retail BI")
    st.markdown("**Version:** 2.0 (Production Ready)")
    st.markdown("**Data Source:** UCI Online Retail")
    st.markdown("---")

    st.subheader("Data Warehouse Status")
    try:
        ensure_warehouse_database()
    except Exception as e:
        st.error(f"⚠️ **Warehouse Initialization Error:** {e}")
    status = check_artifact_status()
    for name, is_ready in status.items():
        icon = "🟢" if is_ready else "🔴"
        st.write(f"{icon} **{name}**")

    st.markdown("---")
    if st.button("🔄 Clear App Cache", help="Invalidate cached query results and reload data from disk"):
        st.cache_data.clear()
        st.success("Cache cleared successfully!")

    st.markdown("---")
    st.caption("E-Commerce Intelligence System | Portfolio Project")

# ──────────────────────────────────────────────
# HERO SECTION
# ──────────────────────────────────────────────
st.markdown('<div class="main-header">Smart Retail Analytics & Recommendation Warehouse</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Enterprise Business Intelligence, RFM Customer Clustering, and Apriori Basket Recommendations</div>', unsafe_allow_html=True)

# Check warehouse readiness
if not status.get("Warehouse DB", False):
    st.error("""
    ⚠️ **Warehouse Database (`retail_warehouse.db`) not detected!**  
    Please run the build pipeline first using:  
    `python run_pipeline.py` or `python build_warehouse.py`
    """)
    st.stop()

# ──────────────────────────────────────────────
# SYSTEM OVERVIEW METRICS
# ──────────────────────────────────────────────
try:
    kpis = load_kpis()
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Warehouse Revenue", format_currency(kpis["GrossRevenue"], compact=True), help="Cumulative revenue across all valid transactions")
    with col2:
        st.metric("Unique Orders", format_number(kpis["TotalOrders"]), help="Distinct invoices (orders) after removing cancellations and invalid records")
    with col3:
        st.metric("Unique Customers", format_number(kpis["UniqueCustomers"]), help="Unique identified accounts in Dim_Customer")
    with col4:
        st.metric("Active Catalog SKUs", format_number(kpis["UniqueProducts"]), help="Unique products cataloged in Dim_Product")
    with col5:
        st.metric("Average Order Value (AOV)", format_currency(kpis["AvgOrderValue"]), help="Gross Revenue / Total Orders")
except Exception as e:
    st.warning(f"Could not load warehouse KPIs: {e}")

st.markdown("---")

# ──────────────────────────────────────────────
# SYSTEM ARCHITECTURE & NAVIGATION TILES
# ──────────────────────────────────────────────
st.subheader("Explore Analytics Modules")
st.write("Select a module from the sidebar or click into the specialized analytical dashboards below:")

tile_col1, tile_col2, tile_col3 = st.columns(3)

with tile_col1:
    st.markdown("""
    ### 📊 1. Executive Overview
    High-level business telemetry, core retail KPIs, monthly revenue growth trends, and customer retention distributions.
    - **Key Visuals:** Revenue & AOV Trends, MoM Growth, Leading Countries, Top 10 Products.
    """)
    st.page_link("pages/1_Executive_Overview.py", label="Open Executive Overview ➔", icon="📈")

    st.markdown("""
    ### 🛍️ 3. Product Analytics
    SKU-level performance, Pareto revenue contribution, order frequency, and geographic catalog demand.
    - **Key Visuals:** Volume vs Revenue Bubble Chart, Top SKUs, Searchable Product Catalog.
    """)
    st.page_link("pages/3_Product_Analytics.py", label="Open Product Analytics ➔", icon="📦")

with tile_col2:
    st.markdown("""
    ### 📈 2. Sales Analytics
    OLAP multi-dimensional drill-downs across Time (Year → Quarter → Month), Day of Week, and Continental Regions.
    - **Key Visuals:** Drill-Down Hierarchies, Day-of-Week Patterns, Continental Share Donut.
    """)
    st.page_link("pages/2_Sales_Analytics.py", label="Open Sales Analytics ➔", icon="📊")

    st.markdown("""
    ### 🎯 4. Customer Segmentation
    Unsupervised Machine Learning customer grouping via Recency, Frequency, and Monetary (RFM) K-Means clustering.
    - **Key Visuals:** K-Means vs RFM Score Segments, 2D/3D Scatter Spaces, Elbow/Silhouette Validation.
    """)
    st.page_link("pages/4_Customer_Segmentation.py", label="Open Customer Segmentation ➔", icon="👥")

with tile_col3:
    st.markdown("""
    ### 🛒 5. Market Basket Analysis
    Association rule mining with Apriori algorithm ($min\\_support=0.02$, $min\\_confidence=0.30$, $min\\_lift=1.0$).
    - **Key Visuals:** Interactive Rule Explorer, Support-Confidence-Lift Scatter, Product Recommender.
    """)
    st.page_link("pages/5_Market_Basket_Analysis.py", label="Open Market Basket Analysis ➔", icon="💡")

    st.markdown("""
    ### 🗄️ 6. Warehouse Explorer
    Direct inspection of the SQLite star schema, table schemas, live row counts, and safe read-only SQL querying.
    - **Key Visuals:** Star Schema Specs, Predefined OLAP Queries, Interactive Safe SQL Console.
    """)
    st.page_link("pages/6_Warehouse_Explorer.py", label="Open Warehouse Explorer ➔", icon="🔍")

st.markdown("---")

# ──────────────────────────────────────────────
# END-TO-END PIPELINE ARCHITECTURE
# ──────────────────────────────────────────────
with st.expander("🏗️ View End-to-End System Architecture (Click to expand)", expanded=False):
    st.markdown("""
    ```
    ┌────────────────────────────────────────────────────────────────────────┐
    │                       UCI Online Retail Dataset                        │
    │                      (541,909 Raw Invoice Rows)                        │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                      Data Cleaning ETL Pipeline                        │
    │     - Remove Cancellations ('C' prefix) & Non-positive Quantities       │
    │     - Filter Zero/Negative Prices & Missing Customer IDs                │
    │     - Deduplicate & Compute TotalAmount = Quantity * UnitPrice         │
    │                    Result: 392,692 Clean Records                       │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                 SQLite Star Schema Data Warehouse                      │
    │    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
    │    │   Dim_Time   │     │ Dim_Customer │     │ Dim_Product  │          │
    │    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘          │
    │           │                    │                    │                  │
    │           └──────────────┬─────┴────────────────────┘                  │
    │                          ▼                                             │
    │                  ┌──────────────┐                                      │
    │                  │  Fact_Sales  │ ◄────── ┌──────────────┐             │
    │                  └──────────────┘         │  Dim_Region  │             │
    │                                           └──────────────┘             │
    └──────────────────┬────────────────────────────────┬────────────────────┘
                       │                                │
                       ▼                                ▼
    ┌────────────────────────────────────┐  ┌────────────────────────────────┐
    │       Customer Intelligence        │  │     Market Basket Analysis     │
    │  - RFM Feature Engineering         │  │  - Transaction Baskets         │
    │  - K-Means Clustering (K=4)        │  │  - Apriori Algorithm           │
    │  - Defensible Multi-Metric Labels  │  │  - Support, Confidence, Lift   │
    │  - Silhouette & Elbow Validation   │  │  - Product Recommender Rules   │
    └──────────────────┬─────────────────┘  └────────────────┬───────────────┘
                       │                                     │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │             Interactive Streamlit Business Intelligence Suite          │
    │         6 Multi-Page Analytical Dashboards with Plotly Visuals         │
    └────────────────────────────────────────────────────────────────────────┘
    ```
    """)

render_footer()
