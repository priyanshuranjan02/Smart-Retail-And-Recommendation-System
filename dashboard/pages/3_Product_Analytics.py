"""
Product Analytics Dashboard — Smart Retail Analytics
SKU ranking, Pareto contribution, volume vs price dynamics, and searchable catalog.
"""

import sys
import os

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from components.data_loader import (
    load_top_products,
    load_countries_list,
    get_db_connection,
)
from components.metrics import format_currency, format_number, format_pct
from components.charts import plot_top_products
from components.insights import render_footer

st.set_page_config(page_title="Product Analytics | Smart Retail", page_icon="📦", layout="wide")

st.title("📦 Product & SKU Analytics")
st.markdown("Detailed product performance, volume vs revenue contribution, order frequency, and catalog search.")

# ──────────────────────────────────────────────
# FILTERS & CONTROLS
# ──────────────────────────────────────────────
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    top_n = st.selectbox("Top N Products:", options=[10, 20, 50, 100], index=0)
with f_col2:
    rank_by = st.selectbox("Rank By:", options=["TotalRevenue", "TotalUnitsSold", "TimesOrdered"], index=0,
                           format_func=lambda x: "Gross Revenue (£)" if x == "TotalRevenue" else ("Units Sold" if x == "TotalUnitsSold" else "Order Frequency"))
with f_col3:
    countries = load_countries_list()
    selected_country = st.selectbox("Filter by Country:", options=countries, index=0)

order_by_key = "revenue" if rank_by == "TotalRevenue" else ("units" if rank_by == "TotalUnitsSold" else "orders")
df_products = load_top_products(limit=top_n, order_by=order_by_key, country=selected_country)

# ──────────────────────────────────────────────
# TOP PRODUCTS VISUALIZATION
# ──────────────────────────────────────────────
p_col1, p_col2 = st.columns([3, 2])

with p_col1:
    title_text = f"Top {top_n} Products Ranked by {'Revenue' if order_by_key == 'revenue' else ('Units' if order_by_key == 'units' else 'Orders')}"
    fig_prod = plot_top_products(df_products, metric=rank_by, title=title_text)
    st.plotly_chart(fig_prod, use_container_width=True)

with p_col2:
    # Scatter of Price vs Units Sold
    fig_bubble = px.scatter(
        df_products,
        x="AvgPrice",
        y="TotalUnitsSold",
        size="TotalRevenue",
        color="TotalRevenue",
        hover_name="Description",
        hover_data=["StockCode", "TimesOrdered", "AvgPrice", "TotalRevenue"],
        title="<b>Price vs Units Sold (Bubble size = Revenue)</b>",
        labels={"AvgPrice": "Avg Unit Price (£)", "TotalUnitsSold": "Units Sold"}
    )
    fig_bubble.update_layout(
        margin=dict(l=30, r=30, t=50, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────────
# SEARCHABLE PRODUCT CATALOG
# ──────────────────────────────────────────────
st.subheader("🔍 Searchable Product Catalog")
search_term = st.text_input("Search catalog by Product Description or StockCode:", placeholder="e.g. TEACUP, BAG, HEART, 22423")

conn = get_db_connection()
if search_term.strip():
    query_term = f"%{search_term.strip()}%"
    sql = """
        SELECT
            p.StockCode,
            COALESCE(p.Description, 'Unknown Product') AS Description,
            p.AvgUnitPrice,
            COUNT(DISTINCT f.InvoiceNo)                 AS InvoicesOrdered,
            SUM(f.Quantity)                             AS TotalUnitsSold,
            ROUND(SUM(f.TotalAmount), 2)                AS TotalRevenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS RevenuePerInvoice
        FROM Fact_Sales f
        JOIN Dim_Product p ON f.ProductKey = p.ProductKey
        WHERE p.Description LIKE ? OR p.StockCode LIKE ?
        GROUP BY p.StockCode, p.Description, p.AvgUnitPrice
        ORDER BY TotalRevenue DESC
        LIMIT 100
    """
    df_catalog = pd.read_sql_query(sql, conn, params=(query_term, query_term))
else:
    sql = """
        SELECT
            p.StockCode,
            COALESCE(p.Description, 'Unknown Product') AS Description,
            p.AvgUnitPrice,
            COUNT(DISTINCT f.InvoiceNo)                 AS InvoicesOrdered,
            SUM(f.Quantity)                             AS TotalUnitsSold,
            ROUND(SUM(f.TotalAmount), 2)                AS TotalRevenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS RevenuePerInvoice
        FROM Fact_Sales f
        JOIN Dim_Product p ON f.ProductKey = p.ProductKey
        GROUP BY p.StockCode, p.Description, p.AvgUnitPrice
        ORDER BY TotalRevenue DESC
        LIMIT 50
    """
    df_catalog = pd.read_sql_query(sql, conn)

conn.close()

st.write(f"Displaying **{len(df_catalog)}** matching products:")
st.dataframe(
    df_catalog.style.format({
        "AvgUnitPrice": "£{:,.2f}",
        "TotalRevenue": "£{:,.2f}",
        "RevenuePerInvoice": "£{:,.2f}",
        "InvoicesOrdered": "{:,}",
        "TotalUnitsSold": "{:,}"
    }),
    use_container_width=True
)

render_footer()
