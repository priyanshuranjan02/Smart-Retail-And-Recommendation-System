"""
Unit and integration tests for SQLite star schema warehouse creation and integrity.
"""

import sqlite3
import pandas as pd
from build_warehouse import (
    build_dim_time,
    build_dim_region,
    build_dim_product,
    build_dim_customer,
    build_fact_sales,
)


def test_dim_time_generation(sample_cleaned_df):
    """Verify Dim_Time correctly extracts calendar components and surrogate TimeKey."""
    dim_time = build_dim_time(sample_cleaned_df)
    assert len(dim_time) == 5  # 5 distinct dates in fixture
    assert "TimeKey" in dim_time.columns
    assert "FullDate" in dim_time.columns
    assert "Year" in dim_time.columns
    assert "Quarter" in dim_time.columns
    assert "Month" in dim_time.columns
    assert "DayOfWeek" in dim_time.columns


def test_dim_region_mapping(sample_cleaned_df):
    """Verify Dim_Region generates surrogate keys and categorizes regions."""
    dim_region, lookup = build_dim_region(sample_cleaned_df)
    assert len(dim_region) == 3  # UK, France, Germany
    assert "United Kingdom" in lookup
    assert lookup["United Kingdom"] == 1
    assert dim_region.loc[dim_region["Country"] == "United Kingdom", "Region"].iloc[0] == "Europe"


def test_dim_product_aggregation(sample_cleaned_df):
    """Verify Dim_Product calculates average unit prices and order frequency."""
    dim_product, lookup = build_dim_product(sample_cleaned_df)
    assert len(dim_product) == 3  # ITEM_A, ITEM_B, ITEM_C
    assert "ITEM_A" in lookup
    item_a_row = dim_product[dim_product["StockCode"] == "ITEM_A"].iloc[0]
    assert item_a_row["AvgUnitPrice"] == 2.50
    assert item_a_row["TimesOrdered"] == 2


def test_dim_customer_aggregation(sample_cleaned_df):
    """Verify Dim_Customer aggregates lifetime spend and orders."""
    dim_customer, lookup = build_dim_customer(sample_cleaned_df)
    assert len(dim_customer) == 3
    cust_1 = dim_customer[dim_customer["CustomerID"] == 10001].iloc[0]
    # In fixture: Invoice 500001 (25+20=45) and Invoice 500004 (32) = 77.00
    assert cust_1["TotalSpend"] == 77.00
    assert cust_1["TotalOrders"] == 2


def test_warehouse_fact_and_foreign_key_integrity(in_memory_warehouse, sample_cleaned_df):
    """Verify Fact_Sales has valid foreign keys referencing dimension tables."""
    cursor = in_memory_warehouse.cursor()

    # Fact sales count
    fact_count = cursor.execute("SELECT COUNT(*) FROM Fact_Sales").fetchone()[0]
    assert fact_count == len(sample_cleaned_df)

    # Reconcile revenue
    warehouse_rev = cursor.execute("SELECT ROUND(SUM(TotalAmount), 2) FROM Fact_Sales").fetchone()[0]
    expected_rev = round(float(sample_cleaned_df["TotalAmount"].sum()), 2)
    assert warehouse_rev == expected_rev

    # Verify all foreign keys resolve cleanly
    orphan_time = cursor.execute("SELECT COUNT(*) FROM Fact_Sales f LEFT JOIN Dim_Time t ON f.TimeKey = t.TimeKey WHERE t.TimeKey IS NULL").fetchone()[0]
    orphan_cust = cursor.execute("SELECT COUNT(*) FROM Fact_Sales f LEFT JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey WHERE c.CustomerKey IS NULL").fetchone()[0]
    orphan_prod = cursor.execute("SELECT COUNT(*) FROM Fact_Sales f LEFT JOIN Dim_Product p ON f.ProductKey = p.ProductKey WHERE p.ProductKey IS NULL").fetchone()[0]
    orphan_reg  = cursor.execute("SELECT COUNT(*) FROM Fact_Sales f LEFT JOIN Dim_Region r ON f.RegionKey = r.RegionKey WHERE r.RegionKey IS NULL").fetchone()[0]

    assert orphan_time == 0
    assert orphan_cust == 0
    assert orphan_prod == 0
    assert orphan_reg == 0
