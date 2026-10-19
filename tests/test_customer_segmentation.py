"""
Unit tests for customer RFM feature engineering, clustering, and defensible labeling.
"""

import pandas as pd
import numpy as np
from customer_segmentation import (
    calculate_rfm,
    evaluate_kmeans_candidates,
    assign_defensible_cluster_labels,
    calculate_rfm_scores,
)
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


def test_calculate_rfm(sample_cleaned_df):
    """Verify RFM values calculated per customer."""
    rfm = calculate_rfm(sample_cleaned_df)
    assert len(rfm) == 3  # 3 distinct customers
    assert set(rfm.columns) == {"CustomerID", "Recency", "Frequency", "Monetary"}

    cust_1 = rfm[rfm["CustomerID"] == 10001].iloc[0]
    assert cust_1["Frequency"] == 2
    assert cust_1["Monetary"] == 77.00
    assert cust_1["Recency"] > 0


def test_calculate_rfm_scores():
    """Verify independent 1-5 quantile scores for R, F, and M without tie errors."""
    # Synthetic dataset with duplicates and wide range
    rfm_df = pd.DataFrame({
        "CustomerID": range(1, 11),
        "Recency": [5, 10, 10, 25, 40, 80, 100, 150, 200, 300],
        "Frequency": [1, 1, 1, 2, 2, 3, 5, 8, 12, 25],
        "Monetary": [50.0, 50.0, 100.0, 150.0, 200.0, 450.0, 800.0, 1500.0, 3000.0, 10000.0]
    })
    scored = calculate_rfm_scores(rfm_df)
    assert "R_Score" in scored.columns
    assert "F_Score" in scored.columns
    assert "M_Score" in scored.columns
    assert "RFM_Score" in scored.columns
    assert "RFM_Segment" in scored.columns

    # Verify R_Score: lowest recency gets score 5
    assert scored.loc[scored["Recency"] == 5, "R_Score"].iloc[0] == 5
    # Verify M_Score: highest spend gets score 5
    assert scored.loc[scored["Monetary"] == 10000.0, "M_Score"].iloc[0] == 5


def test_assign_defensible_cluster_labels():
    """Verify deterministic ranking assigns Champions to the cluster with lowest recency and highest spend."""
    rfm_clusters = pd.DataFrame({
        "CustomerID": range(1, 9),
        "Cluster": [0, 0, 1, 1, 2, 2, 3, 3],
        "Recency": [6, 8, 15, 18, 45, 50, 220, 260],
        "Frequency": [70, 85, 20, 24, 4, 3, 1, 1],
        "Monetary": [110000.0, 130000.0, 12000.0, 14000.0, 1200.0, 1400.0, 300.0, 400.0]
    })

    rfm_labeled, label_map, summary = assign_defensible_cluster_labels(rfm_clusters, "Cluster")
    assert label_map[0] == "Champions (High-Value)"
    assert label_map[1] == "Loyal Customers"
    assert label_map[2] == "Regular Customers"
    assert label_map[3] == "At-Risk (Low-Value)"
    assert len(summary) == 4
