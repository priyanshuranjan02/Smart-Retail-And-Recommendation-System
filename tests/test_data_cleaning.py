"""
Unit tests for data cleaning ETL transformations.
"""

import pandas as pd
import numpy as np
from data_cleaning import clean_dataset


def test_clean_dataset_removes_cancellations(sample_raw_transactions):
    """Verify invoices with 'C' prefixes are properly removed."""
    cleaned_df, stats = clean_dataset(sample_raw_transactions)
    assert not any(cleaned_df["InvoiceNo"].astype(str).str.startswith("C"))
    assert stats["cancelled_rows"] == 1


def test_clean_dataset_removes_negative_and_zero_quantities(sample_raw_transactions):
    """Verify non-positive quantities are filtered out."""
    cleaned_df, stats = clean_dataset(sample_raw_transactions)
    assert (cleaned_df["Quantity"] > 0).all()
    assert stats["non_positive_qty_rows"] == 2


def test_clean_dataset_removes_invalid_unit_prices(sample_raw_transactions):
    """Verify zero and negative prices are filtered out."""
    cleaned_df, stats = clean_dataset(sample_raw_transactions)
    assert (cleaned_df["UnitPrice"] > 0).all()


def test_clean_dataset_removes_missing_customer_ids(sample_raw_transactions):
    """Verify records with missing CustomerID are dropped."""
    cleaned_df, stats = clean_dataset(sample_raw_transactions)
    assert cleaned_df["CustomerID"].notnull().all()
    assert stats["missing_customer_id_rows"] == 1
    assert pd.api.types.is_integer_dtype(cleaned_df["CustomerID"])


def test_clean_dataset_deduplication(sample_raw_transactions):
    """Verify duplicate rows are pruned."""
    cleaned_df, stats = clean_dataset(sample_raw_transactions)
    assert not cleaned_df.duplicated().any()
    assert stats["duplicate_rows"] == 1


def test_clean_dataset_total_amount_calculation(sample_raw_transactions):
    """Verify TotalAmount equals round(Quantity * UnitPrice, 2)."""
    cleaned_df, _ = clean_dataset(sample_raw_transactions)
    expected_amount = (cleaned_df["Quantity"] * cleaned_df["UnitPrice"]).round(2)
    pd.testing.assert_series_equal(cleaned_df["TotalAmount"], expected_amount, check_names=False)
