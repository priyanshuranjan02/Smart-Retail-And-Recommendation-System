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


# ──────────────────────────────────────────────
# TESTS FOR acquire_raw_dataset (SSL & ATOMICITY)
# ──────────────────────────────────────────────

import os
import ssl
import urllib.request
import urllib.error
import pytest
from unittest.mock import MagicMock
from data_cleaning import acquire_raw_dataset


def test_acquire_raw_dataset_existing_file(tmp_path, monkeypatch):
    """Verify that an existing file is preserved and no network call is made."""
    test_file = tmp_path / "OnlineRetail.xlsx"
    test_file.write_bytes(b"EXISTING_DATA")

    mock_urlopen = MagicMock()
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = acquire_raw_dataset(str(test_file))
    assert result == str(test_file)
    assert test_file.read_bytes() == b"EXISTING_DATA"
    mock_urlopen.assert_not_called()


def test_acquire_raw_dataset_successful_download(tmp_path, monkeypatch):
    """Verify verified download writes file atomically and cleans temp file."""
    test_file = tmp_path / "target.xlsx"
    payload = b"MOCK_EXCEL_STREAM_PAYLOAD"

    mock_response = MagicMock()
    # Return payload on first chunk, then empty bytes to simulate EOF
    mock_response.read.side_effect = [payload, b""]
    mock_response.__enter__.return_value = mock_response

    mock_urlopen = MagicMock(return_value=mock_response)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    result = acquire_raw_dataset(str(test_file))
    assert result == str(test_file)
    assert os.path.exists(test_file)
    assert test_file.read_bytes() == payload
    # Verify temp file does not remain
    assert not os.path.exists(f"{test_file}.tmp")

    # Verify an SSL context was passed
    call_kwargs = mock_urlopen.call_args[1]
    assert "context" in call_kwargs
    assert isinstance(call_kwargs["context"], ssl.SSLContext)


def test_acquire_raw_dataset_ssl_verification_failure(tmp_path, monkeypatch):
    """Verify SSL verification failure raises descriptive RuntimeError without partial files."""
    test_file = tmp_path / "untrusted.xlsx"

    ssl_error = ssl.SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
    mock_urlopen = MagicMock(side_effect=ssl_error)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        acquire_raw_dataset(str(test_file))

    err_msg = str(exc_info.value)
    assert "SSL certificate verification failed" in err_msg
    assert "certifi" in err_msg
    # Ensure neither partial target nor temp file remains
    assert not os.path.exists(test_file)
    assert not os.path.exists(f"{test_file}.tmp")


def test_acquire_raw_dataset_url_error_with_ssl_reason(tmp_path, monkeypatch):
    """Verify URLError wrapping SSL verification failure raises clear guidance."""
    test_file = tmp_path / "ssl_url_fail.xlsx"

    url_error = urllib.error.URLError(reason="[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed")
    mock_urlopen = MagicMock(side_effect=url_error)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        acquire_raw_dataset(str(test_file))

    err_msg = str(exc_info.value)
    assert "SSL certificate verification failed" in err_msg
    assert not os.path.exists(test_file)
    assert not os.path.exists(f"{test_file}.tmp")


def test_acquire_raw_dataset_interrupted_download_cleans_temp_file(tmp_path, monkeypatch):
    """Verify interrupted stream raises error and removes orphaned .tmp file."""
    test_file = tmp_path / "interrupted.xlsx"

    mock_response = MagicMock()
    mock_response.read.side_effect = [b"PARTIAL_CHUNK", ConnectionResetError("Connection reset by peer")]
    mock_response.__enter__.return_value = mock_response

    mock_urlopen = MagicMock(return_value=mock_response)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        acquire_raw_dataset(str(test_file))

    assert "Failed to download dataset" in str(exc_info.value)
    # Crucial: target file must NOT exist (no corrupt partial file treated as valid)
    assert not os.path.exists(test_file)
    assert not os.path.exists(f"{test_file}.tmp")


def test_acquire_raw_dataset_general_network_failure(tmp_path, monkeypatch):
    """Verify general network error raises clear RuntimeError and leaves no files."""
    test_file = tmp_path / "net_fail.xlsx"

    mock_urlopen = MagicMock(side_effect=urllib.error.URLError("Connection refused"))
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(RuntimeError) as exc_info:
        acquire_raw_dataset(str(test_file))

    assert "Failed to download dataset" in str(exc_info.value)
    assert not os.path.exists(test_file)
    assert not os.path.exists(f"{test_file}.tmp")

