"""
Unit tests for Streamlit dashboard data loading utilities and graceful error handling.
"""

import os
import pytest
import pandas as pd
from dashboard.components.data_loader import (
    check_artifact_status,
    load_countries_list,
    load_kpis,
    load_customer_segments,
    load_association_rules,
    load_clustering_validation,
    load_warehouse_tables,
)


def test_check_artifact_status():
    """Verify artifact health checker returns boolean dict."""
    status = check_artifact_status()
    assert isinstance(status, dict)
    assert "Warehouse DB" in status
    assert "Cleaned CSV" in status
    assert "Customer Segments" in status


def test_load_countries_list():
    """Verify countries loader returns list starting with 'All'."""
    countries = load_countries_list()
    assert isinstance(countries, list)
    assert len(countries) > 0
    assert countries[0] == "All"


def test_load_kpis_live():
    """Verify loading KPIs from live warehouse returns expected dictionary keys."""
    kpis = load_kpis()
    assert "GrossRevenue" in kpis
    assert "TotalOrders" in kpis
    assert "UniqueCustomers" in kpis
    assert "AvgOrderValue" in kpis
    assert kpis["GrossRevenue"] > 0
    assert kpis["TotalOrders"] > 0


def test_load_customer_segments_live():
    """Verify customer segments dataset loads with required columns."""
    df_seg = load_customer_segments()
    assert not df_seg.empty
    expected_cols = {"CustomerID", "Recency", "Frequency", "Monetary", "Segment", "RFM_Score", "RFM_Segment"}
    assert expected_cols.issubset(set(df_seg.columns))


def test_load_clustering_validation_live():
    """Verify clustering validation JSON loads with required metadata."""
    val = load_clustering_validation()
    assert "tested_k" in val
    assert "selected_k" in val
    assert "selected_k_silhouette" in val
    assert "cluster_profiles" in val
    assert val["selected_k"] == 4


def test_load_association_rules_live():
    """Verify association rules dataset loads with required columns."""
    rules = load_association_rules()
    assert not rules.empty
    expected_cols = {"antecedents", "consequents", "support", "confidence", "lift", "Insight"}
    assert expected_cols.issubset(set(rules.columns))


def test_load_warehouse_tables_live():
    """Verify warehouse table row counts are retrieved."""
    tables_df = load_warehouse_tables()
    assert len(tables_df) == 5
    assert set(tables_df["Table"]) == {"Dim_Time", "Dim_Customer", "Dim_Product", "Dim_Region", "Fact_Sales"}
