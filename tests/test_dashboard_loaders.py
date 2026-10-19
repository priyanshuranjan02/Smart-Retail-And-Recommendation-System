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
    get_db_connection,
    ensure_warehouse_database,
    DB_PATH,
    CLEANED_CSV_PATH,
)


@pytest.fixture(autouse=True, scope="module")
def ensure_warehouse_exists():
    """Ensure retail_warehouse.db exists for dashboard loader tests."""
    if not os.path.exists(DB_PATH) and os.path.exists(CLEANED_CSV_PATH):
        from build_warehouse import build_warehouse, SCHEMA_FILE
        build_warehouse(CLEANED_CSV_PATH, DB_PATH, SCHEMA_FILE, force=True, backup=False)


def test_get_db_connection_missing_raises():
    """Verify get_db_connection raises FileNotFoundError when database file does not exist."""
    import dashboard.components.data_loader as dl
    original_path = dl.DB_PATH
    try:
        dl.DB_PATH = "/tmp/non_existent_retail_warehouse_99999.db"
        with pytest.raises(FileNotFoundError, match="Warehouse database not found"):
            dl.get_db_connection()
    finally:
        dl.DB_PATH = original_path


def test_ensure_warehouse_database_creates_missing(tmp_path):
    """Verify ensure_warehouse_database builds a missing database from cleaned CSV."""
    from build_warehouse import SCHEMA_FILE
    import sqlite3

    sample_csv = tmp_path / "sample_cleaned.csv"
    target_db = tmp_path / "created_warehouse.db"

    data = {
        "InvoiceNo": ["500001", "500002"],
        "StockCode": ["PROD_A", "PROD_B"],
        "Description": ["Product Alpha", "Product Beta"],
        "Quantity": [2, 3],
        "UnitPrice": [10.0, 15.0],
        "CustomerID": [101, 102],
        "InvoiceDate": ["2023-01-01 10:00:00", "2023-01-02 11:30:00"],
        "Country": ["United Kingdom", "France"],
        "TotalAmount": [20.0, 45.0],
    }
    pd.DataFrame(data).to_csv(sample_csv, index=False)

    assert not target_db.exists()

    result_path = ensure_warehouse_database(
        db_path=str(target_db),
        cleaned_csv_path=str(sample_csv),
        schema_path=SCHEMA_FILE
    )

    assert result_path == str(target_db)
    assert target_db.exists()

    # Verify tables and foreign key integrity
    conn = sqlite3.connect(str(target_db))
    cur = conn.cursor()
    fact_count = cur.execute("SELECT COUNT(*) FROM Fact_Sales").fetchone()[0]
    rev_sum = cur.execute("SELECT SUM(TotalAmount) FROM Fact_Sales").fetchone()[0]
    conn.close()

    assert fact_count == 2
    assert rev_sum == 65.0


def test_ensure_warehouse_database_reuses_existing(tmp_path, monkeypatch):
    """Verify ensure_warehouse_database reuses an existing database without rebuilding."""
    existing_db = tmp_path / "existing.db"
    existing_db.write_text("dummy database content")
    mtime_before = existing_db.stat().st_mtime_ns

    # If build_warehouse is called, raise an assertion error
    def mock_build_warehouse(*args, **kwargs):
        raise AssertionError("build_warehouse should not be called when database exists")

    monkeypatch.setattr("build_warehouse.build_warehouse", mock_build_warehouse)

    result_path = ensure_warehouse_database(
        db_path=str(existing_db),
        cleaned_csv_path=str(tmp_path / "unused.csv"),
        schema_path=str(tmp_path / "unused.sql")
    )

    assert result_path == str(existing_db)
    assert existing_db.read_text() == "dummy database content"
    assert existing_db.stat().st_mtime_ns == mtime_before


def test_ensure_warehouse_database_failed_build_cleans_up(tmp_path, monkeypatch):
    """Verify a failed build leaves no corrupt target database or orphaned temporary file."""
    from build_warehouse import SCHEMA_FILE

    sample_csv = tmp_path / "sample_cleaned.csv"
    target_db = tmp_path / "unbuilt.db"

    data = {
        "InvoiceNo": ["500001"],
        "StockCode": ["PROD_A"],
        "Description": ["Product Alpha"],
        "Quantity": [1],
        "UnitPrice": [10.0],
        "CustomerID": [101],
        "InvoiceDate": ["2023-01-01 10:00:00"],
        "Country": ["United Kingdom"],
        "TotalAmount": [10.0],
    }
    pd.DataFrame(data).to_csv(sample_csv, index=False)

    def failing_builder(*args, **kwargs):
        temp_file = kwargs.get("db_file")
        if temp_file:
            with open(temp_file, "w") as f:
                f.write("corrupted partial content")
        raise RuntimeError("Simulated build error during table population")

    monkeypatch.setattr("build_warehouse.build_warehouse", failing_builder)

    with pytest.raises(RuntimeError, match="Simulated build error"):
        ensure_warehouse_database(
            db_path=str(target_db),
            cleaned_csv_path=str(sample_csv),
            schema_path=SCHEMA_FILE
        )

    # Confirm target database was never created
    assert not target_db.exists()

    # Confirm no leftover .tmp files remain in directory
    temp_files = list(tmp_path.glob("*.tmp*"))
    assert len(temp_files) == 0


def test_ensure_warehouse_database_missing_prerequisites_raises(tmp_path):
    """Verify clear FileNotFoundError is raised when prerequisite files are missing."""
    from build_warehouse import SCHEMA_FILE

    target_db = tmp_path / "test.db"
    missing_csv = tmp_path / "non_existent_cleaned.csv"
    valid_csv = tmp_path / "valid.csv"
    valid_csv.write_text("dummy")
    missing_schema = tmp_path / "non_existent_schema.sql"

    # Missing cleaned CSV
    with pytest.raises(FileNotFoundError, match="Cleaned dataset not found"):
        ensure_warehouse_database(
            db_path=str(target_db),
            cleaned_csv_path=str(missing_csv),
            schema_path=SCHEMA_FILE
        )
    assert not target_db.exists()

    # Missing schema SQL
    with pytest.raises(FileNotFoundError, match="Warehouse schema SQL file not found"):
        ensure_warehouse_database(
            db_path=str(target_db),
            cleaned_csv_path=str(valid_csv),
            schema_path=str(missing_schema)
        )
    assert not target_db.exists()


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
