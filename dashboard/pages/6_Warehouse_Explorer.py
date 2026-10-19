"""
Warehouse Explorer & Star Schema Inspector — Smart Retail Analytics
Schema inspection, live table row counts, predefined OLAP queries, and safe read-only SQL console.
"""

import sys
import os
import time

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.data_loader import (
    get_db_connection,
    load_warehouse_tables,
    load_table_preview,
    run_custom_query,
)
from components.metrics import format_number
from components.insights import render_footer

st.set_page_config(page_title="Warehouse Explorer | Smart Retail", page_icon="🗄️", layout="wide")

st.title("🗄️ Warehouse Schema & SQL Explorer")
st.markdown("Inspect the SQLite star schema architecture, live table row counts, grains, and execute safe analytical SQL.")

# ──────────────────────────────────────────────
# STAR SCHEMA SPECS & ROW COUNTS
# ──────────────────────────────────────────────
st.subheader("1. Star Schema Table Specifications & Live Counts")

try:
    df_tables = load_warehouse_tables()
    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]
    for idx, row in df_tables.iterrows():
        with cols[idx % 5]:
            badge = "🧱 Dimension" if row["Type"] == "Dimension" else "📊 Fact Table"
            st.metric(f"{row['Table']}", format_number(row["RowCount"]), help=badge)
except Exception as e:
    st.error(f"Error loading warehouse tables: {e}")

with st.expander("📐 View Star Schema Table Grains & Key Architecture", expanded=False):
    st.markdown("""
    | Table | Table Type | Grain | Primary / Surrogate Key | Natural Key | Key Foreign Keys |
    |---|---|---|---|---|---|
    | **`Dim_Time`** | Dimension | One row per unique calendar date | `TimeKey` (YYYYMMDD) | `FullDate` | None |
    | **`Dim_Customer`** | Dimension | One row per unique customer | `CustomerKey` (surrogate) | `CustomerID` | None |
    | **`Dim_Product`** | Dimension | One row per unique product SKU | `ProductKey` (surrogate) | `StockCode` | None |
    | **`Dim_Region`** | Dimension | One row per unique country | `RegionKey` (surrogate) | `Country` | None |
    | **`Fact_Sales`** | Fact (Line-item) | One row per invoice line item | `SalesKey` (auto-increment) | `InvoiceNo` | `TimeKey`, `CustomerKey`, `ProductKey`, `RegionKey` |
    """)

st.markdown("---")

# ──────────────────────────────────────────────
# TABLE DATA PREVIEW
# ──────────────────────────────────────────────
st.subheader("2. Table Data Preview")

t_col1, t_col2 = st.columns([1, 2])
with t_col1:
    selected_table = st.selectbox("Select Table to Preview:", options=["Fact_Sales", "Dim_Customer", "Dim_Product", "Dim_Time", "Dim_Region"])
    preview_limit = st.slider("Preview Rows:", min_value=10, max_value=200, value=25, step=10)

df_preview = load_table_preview(selected_table, limit=preview_limit)
st.write(f"Displaying top **{len(df_preview)}** rows of `{selected_table}`:")
st.dataframe(df_preview, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# PREDEFINED ANALYTICAL QUERIES
# ──────────────────────────────────────────────
st.subheader("3. Predefined OLAP Queries")
st.caption("Select a curated business intelligence query to inspect the underlying SQL and view instant results:")

PREDEFINED_QUERIES = {
    "Total Sales by Month (Q1)": """
        SELECT
            t.Year,
            t.MonthName,
            COUNT(DISTINCT f.InvoiceNo)  AS TotalOrders,
            SUM(f.Quantity)              AS TotalUnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS TotalRevenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year, t.Month, t.MonthName
        ORDER BY t.Year, t.Month;
    """,
    "Top 10 International Markets (Q2)": """
        SELECT
            r.Country,
            r.Region,
            COUNT(DISTINCT f.InvoiceNo)   AS Orders,
            COUNT(DISTINCT f.CustomerKey) AS Customers,
            ROUND(SUM(f.TotalAmount), 2)  AS Revenue,
            ROUND(SUM(f.TotalAmount) * 100.0 / (SELECT SUM(TotalAmount) FROM Fact_Sales), 2) AS SharePct
        FROM Fact_Sales f
        JOIN Dim_Region r ON f.RegionKey = r.RegionKey
        GROUP BY r.Country, r.Region
        ORDER BY Revenue DESC
        LIMIT 10;
    """,
    "Top 10 Revenue Generating SKUs (Q3)": """
        SELECT
            p.StockCode,
            p.Description,
            SUM(f.Quantity)              AS UnitsSold,
            COUNT(DISTINCT f.InvoiceNo)  AS TimesOrdered,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue
        FROM Fact_Sales f
        JOIN Dim_Product p ON f.ProductKey = p.ProductKey
        GROUP BY p.StockCode, p.Description
        ORDER BY Revenue DESC
        LIMIT 10;
    """,
    "Repeat vs One-Time Buyer Retention (KPI)": """
        SELECT
            CASE
                WHEN OrderCount = 1 THEN 'One-Time Buyer'
                WHEN OrderCount BETWEEN 2 AND 5 THEN 'Returning (2-5 orders)'
                WHEN OrderCount > 5 THEN 'Loyal (6+ orders)'
            END                          AS CustomerType,
            COUNT(*)                     AS CustomerCount,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT CustomerKey) FROM Fact_Sales), 2) AS Pct
        FROM (
            SELECT CustomerKey, COUNT(DISTINCT InvoiceNo) AS OrderCount
            FROM Fact_Sales
            GROUP BY CustomerKey
        )
        GROUP BY CustomerType
        ORDER BY CustomerCount DESC;
    """
}

selected_query_name = st.selectbox("Choose a Predefined BI Query:", options=list(PREDEFINED_QUERIES.keys()))
query_sql = PREDEFINED_QUERIES[selected_query_name]

st.code(query_sql.strip(), language="sql")

if st.button("▶️ Execute Predefined Query"):
    start = time.time()
    try:
        df_res = run_custom_query(query_sql)
        elapsed = time.time() - start
        st.success(f"Query returned **{len(df_res)}** rows in **{elapsed*1000:.1f} ms**:")
        st.dataframe(df_res, use_container_width=True)
    except Exception as e:
        st.error(f"Execution Error: {e}")

st.markdown("---")

# ──────────────────────────────────────────────
# SAFE READ-ONLY SQL CONSOLE
# ──────────────────────────────────────────────
st.subheader("4. Safe Read-Only SQL Console")
st.warning("⚠️ **Safety Notice:** This console executes read-only SQL queries (`SELECT`, `WITH`) against the SQLite warehouse. DDL and DML operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`) are strictly forbidden.")

custom_sql = st.text_area(
    "Enter SQL Query:",
    value="SELECT t.Year, r.Region, ROUND(SUM(f.TotalAmount), 2) AS Revenue\nFROM Fact_Sales f\nJOIN Dim_Time t ON f.TimeKey = t.TimeKey\nJOIN Dim_Region r ON f.RegionKey = r.RegionKey\nGROUP BY t.Year, r.Region\nORDER BY Revenue DESC\nLIMIT 20;",
    height=140
)

if st.button("🚀 Run Custom SQL Query"):
    start = time.time()
    try:
        df_custom = run_custom_query(custom_sql, max_rows=500)
        elapsed = time.time() - start
        st.success(f"Executed successfully in **{elapsed*1000:.1f} ms**! Retrieved **{len(df_custom)}** rows:")
        st.dataframe(df_custom, use_container_width=True)
    except Exception as e:
        st.error(f"Query Execution Error: {e}")

render_footer()
