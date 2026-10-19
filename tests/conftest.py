"""
Pytest configuration and synthetic fixtures for Smart Retail Analytics test suite.
Avoids external network dependencies and large file reads.
"""

import os
import sqlite3
import pytest
import pandas as pd
import numpy as np

SCHEMA_SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "warehouse_schema.sql")


@pytest.fixture
def sample_raw_transactions():
    """Synthetic raw transactions dataframe with cancellations, nulls, and valid purchases."""
    return pd.DataFrame({
        "InvoiceNo": ["536365", "536365", "C536366", "536367", "536368", "536369", "536369"],
        "StockCode": ["85123A", "71053", "22633", "84879", "22745", "22748", "22748"],
        "Description": [
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "WHITE METAL LANTERN",
            "HAND WARMER RED RETROSPOT",
            "ASSORTED COLOUR BIRD ORNAMENT",
            "POPPY'S PLAYHOUSE BEDROOM",
            "HAND WARMER BABUSHKA DESIGN",
            "HAND WARMER BABUSHKA DESIGN"  # duplicate row
        ],
        "Quantity": [6, -2, -1, 32, 6, 4, 4],
        "InvoiceDate": [
            "2011-01-01 10:00:00",
            "2011-01-01 10:05:00",
            "2011-01-01 10:10:00",
            "2011-02-15 11:30:00",
            "2011-03-20 14:15:00",
            "2011-04-10 09:20:00",
            "2011-04-10 09:20:00"
        ],
        "UnitPrice": [2.55, 3.39, 1.85, 1.69, 0.0, 2.10, 2.10],
        "CustomerID": [17850.0, 17850.0, 17850.0, 13047.0, np.nan, 12583.0, 12583.0],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom", "France", "France", "France"]
    })


@pytest.fixture
def sample_cleaned_df():
    """Pre-cleaned valid transactions DataFrame for warehouse and analytics testing."""
    return pd.DataFrame({
        "InvoiceNo": ["500001", "500001", "500002", "500003", "500004", "500005"],
        "StockCode": ["ITEM_A", "ITEM_B", "ITEM_A", "ITEM_C", "ITEM_B", "ITEM_C"],
        "Description": ["Product Alpha", "Product Beta", "Product Alpha", "Product Gamma", "Product Beta", "Product Gamma"],
        "Quantity": [10, 5, 20, 2, 8, 15],
        "InvoiceDate": pd.to_datetime([
            "2011-01-10 09:30:00",
            "2011-01-10 09:30:00",
            "2011-02-15 11:00:00",
            "2011-03-20 14:45:00",
            "2011-05-12 16:15:00",
            "2011-06-18 10:20:00"
        ]),
        "UnitPrice": [2.50, 4.00, 2.50, 10.00, 4.00, 10.00],
        "CustomerID": [10001, 10001, 10002, 10003, 10001, 10002],
        "Country": ["United Kingdom", "United Kingdom", "France", "Germany", "United Kingdom", "France"],
        "TotalAmount": [25.00, 20.00, 50.00, 20.00, 32.00, 150.00]
    })


@pytest.fixture
def in_memory_warehouse(sample_cleaned_df):
    """In-memory SQLite warehouse populated using the star schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)

    from build_warehouse import (
        build_dim_time,
        build_dim_region,
        build_dim_product,
        build_dim_customer,
        build_fact_sales
    )

    dim_time = build_dim_time(sample_cleaned_df)
    dim_time.to_sql("Dim_Time", conn, if_exists="append", index=False)

    dim_region, reg_map = build_dim_region(sample_cleaned_df)
    dim_region.to_sql("Dim_Region", conn, if_exists="append", index=False)

    dim_product, prod_map = build_dim_product(sample_cleaned_df)
    dim_product.to_sql("Dim_Product", conn, if_exists="append", index=False)

    dim_customer, cust_map = build_dim_customer(sample_cleaned_df)
    dim_customer.to_sql("Dim_Customer", conn, if_exists="append", index=False)

    fact = build_fact_sales(sample_cleaned_df, cust_map, prod_map, reg_map)
    fact.to_sql("Fact_Sales", conn, if_exists="append", index=False)

    yield conn
    conn.close()
