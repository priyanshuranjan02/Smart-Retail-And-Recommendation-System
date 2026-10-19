"""
Unit tests for Business Intelligence queries and safe SQL execution.
"""

import pytest
from bi_queries import (
    get_kpis,
    get_monthly_sales,
    get_top_products,
    get_top_customers,
    execute_safe_query,
)


def test_get_kpis_accuracy(in_memory_warehouse):
    """Verify get_kpis returns mathematically consistent summary metrics."""
    kpis = get_kpis(in_memory_warehouse)
    assert kpis["TotalOrders"] == 5  # 5 distinct invoices in fixture
    assert kpis["UniqueCustomers"] == 3
    assert kpis["UniqueProducts"] == 3
    assert kpis["TotalUnitsSold"] == 60
    assert kpis["GrossRevenue"] == 297.00
    assert kpis["AvgOrderValue"] == round(297.00 / 5, 2)


def test_get_kpis_with_country_filter(in_memory_warehouse):
    """Verify get_kpis respects country filtering."""
    kpis_uk = get_kpis(in_memory_warehouse, country="United Kingdom")
    assert kpis_uk["UniqueCustomers"] == 1
    assert kpis_uk["GrossRevenue"] == 77.00


def test_get_monthly_sales(in_memory_warehouse):
    """Verify monthly aggregation groups invoices by calendar month."""
    df_monthly = get_monthly_sales(in_memory_warehouse)
    assert len(df_monthly) == 5  # Jan, Feb, Mar, May, June in fixture
    assert "TotalRevenue" in df_monthly.columns
    assert "AvgOrderValue" in df_monthly.columns


def test_get_top_products(in_memory_warehouse):
    """Verify top products ranked properly."""
    df_top = get_top_products(in_memory_warehouse, limit=2, order_by="revenue")
    assert len(df_top) == 2
    # ITEM_C in fixture: 20 + 150 = 170.00
    assert df_top.iloc[0]["StockCode"] == "ITEM_C"
    assert df_top.iloc[0]["TotalRevenue"] == 170.00


def test_execute_safe_query_select_allowed(in_memory_warehouse):
    """Verify valid read-only SELECT queries succeed."""
    df = execute_safe_query(in_memory_warehouse, "SELECT StockCode, Description FROM Dim_Product ORDER BY StockCode")
    assert len(df) == 3
    assert "StockCode" in df.columns


def test_execute_safe_query_blocks_destructive_ddl(in_memory_warehouse):
    """Verify queries containing DROP, DELETE, INSERT, or ALTER raise ValueError."""
    with pytest.raises(ValueError, match="Only read-only SELECT or WITH"):
        execute_safe_query(in_memory_warehouse, "DROP TABLE Dim_Time")

    with pytest.raises(ValueError, match="Disallowed DDL/DML keyword"):
        execute_safe_query(in_memory_warehouse, "SELECT * FROM Fact_Sales; DELETE FROM Dim_Product")
