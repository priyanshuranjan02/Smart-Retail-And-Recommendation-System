"""
Executive Overview Dashboard — Smart Retail Analytics
Core executive KPIs, sales trends, geographic concentration, and customer retention.
"""

import sys
import os

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.data_loader import (
    load_countries_list,
    load_kpis,
    load_monthly_sales,
    load_monthly_growth,
    load_country_sales,
    load_top_products,
    load_retention_data,
)
from components.metrics import format_currency, format_number, format_pct
from components.charts import (
    plot_monthly_revenue_and_growth,
    plot_mom_growth,
    plot_sales_volume_trends,
    plot_top_countries,
    plot_top_products as plot_top_prod,
    plot_retention_pie,
)
from components.insights import render_kpi_definitions_callout, render_footer

st.set_page_config(page_title="Executive Overview | Smart Retail", page_icon="📈", layout="wide")

st.title("📈 Executive Overview")
st.markdown("High-level executive telemetry, revenue momentum, top products, geographic reach, and buyer retention.")

# ──────────────────────────────────────────────
# FILTERS
# ──────────────────────────────────────────────
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    countries = load_countries_list()
    selected_country = st.selectbox("Select Country Filter", options=countries, index=0)

render_kpi_definitions_callout()

# ──────────────────────────────────────────────
# TOP LEVEL KPIS
# ──────────────────────────────────────────────
try:
    kpis = load_kpis(country=selected_country)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.metric("Gross Revenue", format_currency(kpis["GrossRevenue"]), help="Total sales value (£) excluding cancellations")
    with k2:
        st.metric("Total Orders", format_number(kpis["TotalOrders"]), help="Distinct invoices placed")
    with k3:
        st.metric("Unique Customers", format_number(kpis["UniqueCustomers"]), help="Distinct buyer accounts")
    with k4:
        st.metric("Unique Products", format_number(kpis["UniqueProducts"]), help="Distinct SKUs purchased")
    with k5:
        st.metric("Total Units Sold", format_number(kpis["TotalUnitsSold"]), help="Sum of item quantities")
    with k6:
        st.metric("Average Order Value", format_currency(kpis["AvgOrderValue"]), help="Gross Revenue / Total Orders")
except Exception as e:
    st.error(f"Error loading KPIs: {e}")

st.markdown("---")

# ──────────────────────────────────────────────
# REVENUE & GROWTH CHARTS
# ──────────────────────────────────────────────
c_chart1, c_chart2 = st.columns([3, 2])

with c_chart1:
    monthly_df = load_monthly_sales(country=selected_country)
    if not monthly_df.empty:
        fig_rev = plot_monthly_revenue_and_growth(monthly_df)
        st.plotly_chart(fig_rev, use_container_width=True)
    else:
        st.info("No monthly revenue data available for the selected filter.")

with c_chart2:
    growth_df = load_monthly_growth()
    if not growth_df.empty:
        fig_growth = plot_mom_growth(growth_df)
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("No growth data available.")

with st.expander("🔍 View Monthly Sales Data Table"):
    st.dataframe(monthly_df, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# VOLUME & RETENTION
# ──────────────────────────────────────────────
v_col1, v_col2 = st.columns([3, 2])

with v_col1:
    if not monthly_df.empty:
        fig_vol = plot_sales_volume_trends(monthly_df)
        st.plotly_chart(fig_vol, use_container_width=True)

with v_col2:
    retention_df = load_retention_data()
    if not retention_df.empty:
        fig_ret = plot_retention_pie(retention_df)
        st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# GEOGRAPHY & PRODUCT LEADERS
# ──────────────────────────────────────────────
g_col1, g_col2 = st.columns(2)

with g_col1:
    country_df = load_country_sales(limit=10)
    if not country_df.empty:
        fig_country = plot_top_countries(country_df, top_n=10)
        st.plotly_chart(fig_country, use_container_width=True)

with g_col2:
    top_prod_df = load_top_products(limit=10, order_by="revenue", country=selected_country)
    if not top_prod_df.empty:
        fig_prod = plot_top_prod(top_prod_df, metric="TotalRevenue", title="Top 10 Products by Revenue")
        st.plotly_chart(fig_prod, use_container_width=True)

render_footer()
