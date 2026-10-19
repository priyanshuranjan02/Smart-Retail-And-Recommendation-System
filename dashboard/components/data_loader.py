"""
Smart Retail Analytics Dashboard — Centralized Data Loader
Provides cached, thread-safe access to the SQLite Warehouse and analytical artifacts.
"""

import os
import json
import sqlite3
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any, Tuple

# Path configuration relative to repository root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "processed", "retail_warehouse.db")
SEGMENTS_PATH = os.path.join(BASE_DIR, "data", "processed", "customer_segments.csv")
CLUSTERING_VAL_PATH = os.path.join(BASE_DIR, "data", "processed", "clustering_validation.json")
RULES_PATH = os.path.join(BASE_DIR, "data", "processed", "association_rules.csv")
ITEMSETS_PATH = os.path.join(BASE_DIR, "data", "processed", "frequent_itemsets.csv")
MBA_SUMMARY_PATH = os.path.join(BASE_DIR, "data", "processed", "mba_summary.json")
CLEANED_CSV_PATH = os.path.join(BASE_DIR, "data", "cleaned", "online_retail_cleaned.csv")


def check_artifact_status() -> Dict[str, bool]:
    """Check availability of required analytical and warehouse artifacts."""
    return {
        "Cleaned CSV": os.path.exists(CLEANED_CSV_PATH),
        "Warehouse DB": os.path.exists(DB_PATH),
        "Customer Segments": os.path.exists(SEGMENTS_PATH),
        "Clustering Validation": os.path.exists(CLUSTERING_VAL_PATH),
        "Association Rules": os.path.exists(RULES_PATH),
        "Frequent Itemsets": os.path.exists(ITEMSETS_PATH),
        "MBA Summary": os.path.exists(MBA_SUMMARY_PATH),
    }


def get_db_connection() -> sqlite3.Connection:
    """Establish a read-only SQLite connection with foreign keys enabled."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Warehouse database not found at {DB_PATH}. "
            "Please run 'python build_warehouse.py' or 'python run_pipeline.py' first."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@st.cache_data(ttl=3600)
def load_countries_list() -> list[str]:
    """Load distinct countries available in the warehouse."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT DISTINCT Country FROM Dim_Region ORDER BY Country", conn)
        conn.close()
        return ["All"] + df["Country"].tolist()
    except Exception:
        return ["All", "United Kingdom", "Germany", "France", "EIRE"]


@st.cache_data(ttl=3600)
def load_kpis(country: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Load executive summary KPIs with dynamic dimension filters."""
    conn = get_db_connection()
    from bi_queries import get_kpis as _get_kpis
    kpis = _get_kpis(conn, country=country, start_date=start_date, end_date=end_date)
    conn.close()
    return kpis


@st.cache_data(ttl=3600)
def load_monthly_sales(country: Optional[str] = None) -> pd.DataFrame:
    """Load monthly sales trends with optional country filter."""
    conn = get_db_connection()
    from bi_queries import get_monthly_sales as _get_monthly
    df = _get_monthly(conn, country=country)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_monthly_growth() -> pd.DataFrame:
    """Load Month-over-Month growth calculations."""
    conn = get_db_connection()
    from bi_queries import get_monthly_growth as _get_growth
    df = _get_growth(conn)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_country_sales(limit: Optional[int] = None) -> pd.DataFrame:
    """Load sales aggregation by country and region."""
    conn = get_db_connection()
    from bi_queries import get_country_sales as _get_country
    df = _get_country(conn, limit=limit)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_top_products(limit: int = 10, order_by: str = "revenue", country: Optional[str] = None) -> pd.DataFrame:
    """Load top ranked products with contribution metrics."""
    conn = get_db_connection()
    from bi_queries import get_top_products as _get_top
    df = _get_top(conn, limit=limit, order_by=order_by, country=country)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_top_customers(limit: int = 20) -> pd.DataFrame:
    """Load top customers by lifetime spend."""
    conn = get_db_connection()
    from bi_queries import get_top_customers as _get_top_cust
    df = _get_top_cust(conn, limit=limit)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_retention_data() -> pd.DataFrame:
    """Load customer retention purchase frequency distribution."""
    conn = get_db_connection()
    from bi_queries import get_retention_breakdown as _get_retention
    df = _get_retention(conn)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_day_of_week_sales() -> pd.DataFrame:
    """Load sales aggregation by day of week."""
    conn = get_db_connection()
    from bi_queries import get_sales_by_day_of_week as _get_dow
    df = _get_dow(conn)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_region_sales() -> pd.DataFrame:
    """Load revenue aggregated by continental region."""
    conn = get_db_connection()
    from bi_queries import get_sales_by_region as _get_reg
    df = _get_reg(conn)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_customer_segments() -> pd.DataFrame:
    """Load precomputed customer RFM and segmentation assignments."""
    if not os.path.exists(SEGMENTS_PATH):
        raise FileNotFoundError(
            f"Customer segments file not found at {SEGMENTS_PATH}. "
            "Please run 'python customer_segmentation.py' or 'python run_pipeline.py'."
        )
    return pd.read_csv(SEGMENTS_PATH)


@st.cache_data(ttl=3600)
def load_clustering_validation() -> dict:
    """Load K-Means clustering evaluation metrics and business interpretations."""
    if not os.path.exists(CLUSTERING_VAL_PATH):
        raise FileNotFoundError(
            f"Clustering validation metadata not found at {CLUSTERING_VAL_PATH}. "
            "Please run 'python customer_segmentation.py' first."
        )
    with open(CLUSTERING_VAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def load_association_rules() -> pd.DataFrame:
    """Load precomputed Apriori association rules."""
    if not os.path.exists(RULES_PATH):
        raise FileNotFoundError(
            f"Association rules file not found at {RULES_PATH}. "
            "Please run 'python market_basket_analysis.py' or 'python run_pipeline.py'."
        )
    return pd.read_csv(RULES_PATH)


@st.cache_data(ttl=3600)
def load_frequent_itemsets() -> pd.DataFrame:
    """Load precomputed frequent itemsets."""
    if not os.path.exists(ITEMSETS_PATH):
        return pd.DataFrame()
    return pd.read_csv(ITEMSETS_PATH)


@st.cache_data(ttl=3600)
def load_mba_summary() -> dict:
    """Load Market Basket Analysis metadata summary."""
    if not os.path.exists(MBA_SUMMARY_PATH):
        return {}
    with open(MBA_SUMMARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def load_warehouse_tables() -> pd.DataFrame:
    """Retrieve all table names and row counts from SQLite warehouse."""
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = ["Dim_Time", "Dim_Customer", "Dim_Product", "Dim_Region", "Fact_Sales"]
    records = []
    for t in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        records.append({"Table": t, "Type": "Fact" if "Fact" in t else "Dimension", "RowCount": count})
    conn.close()
    return pd.DataFrame(records)


@st.cache_data(ttl=3600)
def load_table_preview(table_name: str, limit: int = 50) -> pd.DataFrame:
    """Load a sample preview of rows from a specific warehouse table."""
    conn = get_db_connection()
    # Whitelist table names to prevent injection
    allowed = ["Dim_Time", "Dim_Customer", "Dim_Product", "Dim_Region", "Fact_Sales"]
    if table_name not in allowed:
        raise ValueError(f"Table '{table_name}' is not an authorized warehouse table.")
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {int(limit)}", conn)
    conn.close()
    return df


def run_custom_query(sql: str, max_rows: int = 200) -> pd.DataFrame:
    """Execute a validated read-only SQL query via bi_queries."""
    conn = get_db_connection()
    from bi_queries import execute_safe_query
    df = execute_safe_query(conn, sql, max_rows=max_rows)
    conn.close()
    return df
