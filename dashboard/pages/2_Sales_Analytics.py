"""
Sales Analytics & OLAP Multi-Dimensional Explorer — Smart Retail Analytics
Drill-down hierarchies, temporal patterns, regional share, and day-of-week sales intelligence.
"""

import sys
import os

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.data_loader import (
    get_db_connection,
    load_countries_list,
    load_monthly_sales,
    load_country_sales,
    load_day_of_week_sales,
    load_region_sales,
)
from components.metrics import format_currency, format_number, format_pct
from components.charts import (
    plot_top_countries,
    plot_day_of_week,
    plot_region_share,
)
from components.insights import render_footer

st.set_page_config(page_title="Sales Analytics | Smart Retail", page_icon="📊", layout="wide")

st.title("📊 Sales Analytics & OLAP Explorer")
st.markdown("Multi-dimensional analysis of sales across Time (Year, Quarter, Month), Geography, and Day-of-Week cadence.")

# ──────────────────────────────────────────────
# OLAP DRILL-DOWN SECTION
# ──────────────────────────────────────────────
st.subheader("1. Temporal Drill-Down: Year ➔ Quarter ➔ Month")
st.caption("Inspect revenue at different granularities as defined in the warehouse BI query suite.")

drill_level = st.radio(
    "Select Granularity Level:",
    options=["Level 1: By Year", "Level 2: By Year & Quarter", "Level 3: By Year, Quarter & Month"],
    horizontal=True
)

conn = get_db_connection()

if drill_level == "Level 1: By Year":
    sql = """
        SELECT
            t.Year,
            COUNT(DISTINCT f.InvoiceNo)  AS Orders,
            SUM(f.Quantity)              AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year
        ORDER BY t.Year
    """
elif drill_level == "Level 2: By Year & Quarter":
    sql = """
        SELECT
            t.Year,
            'Q' || t.Quarter             AS Quarter,
            t.Year || '-Q' || t.Quarter  AS YearQuarter,
            COUNT(DISTINCT f.InvoiceNo)  AS Orders,
            SUM(f.Quantity)              AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year, t.Quarter
        ORDER BY t.Year, t.Quarter
    """
else:
    sql = """
        SELECT
            t.Year,
            'Q' || t.Quarter             AS Quarter,
            t.MonthName,
            t.Year || '-' || PRINTF('%02d', t.Month) AS YearMonth,
            COUNT(DISTINCT f.InvoiceNo)  AS Orders,
            SUM(f.Quantity)              AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year, t.Quarter, t.Month, t.MonthName
        ORDER BY t.Year, t.Month
    """

df_drill = pd.read_sql_query(sql, conn)
conn.close()

c_col1, c_col2 = st.columns([3, 2])
with c_col1:
    x_axis = "Year" if "YearQuarter" not in df_drill.columns and "YearMonth" not in df_drill.columns else ("YearQuarter" if "YearQuarter" in df_drill.columns else "YearMonth")
    st.bar_chart(df_drill, x=x_axis, y="Revenue", color="#1E88E5", use_container_width=True)

with c_col2:
    st.dataframe(df_drill, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# DAY OF WEEK & REGIONAL SALES
# ──────────────────────────────────────────────
st.subheader("2. Operational Cadence & Regional Distribution")

sec2_col1, sec2_col2 = st.columns(2)

with sec2_col1:
    dow_df = load_day_of_week_sales()
    if not dow_df.empty:
        fig_dow = plot_day_of_week(dow_df)
        st.plotly_chart(fig_dow, use_container_width=True)
        with st.expander("View Day-of-Week Statistics"):
            st.dataframe(dow_df[["DayName", "Orders", "UnitsSold", "Revenue", "AvgOrderValue"]], use_container_width=True)

with sec2_col2:
    region_df = load_region_sales()
    if not region_df.empty:
        fig_reg = plot_region_share(region_df)
        st.plotly_chart(fig_reg, use_container_width=True)
        with st.expander("View Regional Revenue Summary"):
            st.dataframe(region_df, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# GEOGRAPHIC REVENUE DISTRIBUTION
# ──────────────────────────────────────────────
st.subheader("3. Country-Level Sales Performance")
st.caption("Top international markets ordered by total revenue and percentage contribution.")

country_df = load_country_sales()
st.dataframe(
    country_df.style.format({
        "TotalRevenue": "£{:,.2f}",
        "RevenueSharePct": "{:.2f}%",
        "TotalOrders": "{:,}",
        "UniqueCustomers": "{:,}",
        "TotalUnitsSold": "{:,}"
    }),
    use_container_width=True
)

render_footer()
