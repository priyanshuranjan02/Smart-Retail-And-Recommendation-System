"""
Unit tests for Market Basket Analysis and Apriori association rules.
"""

import pandas as pd
from market_basket_analysis import (
    build_transaction_baskets,
    find_frequent_itemsets,
    generate_rules,
)


def test_build_transaction_baskets(sample_cleaned_df):
    """Verify clean line items are grouped into unique product name lists per InvoiceNo."""
    baskets = build_transaction_baskets(sample_cleaned_df)
    assert len(baskets) == 5  # 5 distinct invoices in fixture
    # Invoice 500001 has Product Alpha and Product Beta
    assert any(set(["Product Alpha", "Product Beta"]).issubset(set(b)) for b in baskets)


def test_find_frequent_itemsets():
    """Verify Apriori identifies item combinations exceeding support threshold."""
    baskets = [
        ["Bread", "Milk"],
        ["Bread", "Butter"],
        ["Bread", "Milk", "Butter"],
        ["Beer"],
        ["Milk", "Butter"]
    ]
    # min_support = 0.4 (at least 2 of 5 baskets)
    itemsets, basket_df = find_frequent_itemsets(baskets, min_support=0.4)
    assert not itemsets.empty
    assert "support" in itemsets.columns
    assert "itemsets" in itemsets.columns
    assert (itemsets["support"] >= 0.4).all()


def test_generate_rules():
    """Verify association rules generation and metric calculations."""
    baskets = [
        ["Product_A", "Product_B"],
        ["Product_A", "Product_B"],
        ["Product_A", "Product_B"],
        ["Product_C", "Product_D"],
        ["Product_C", "Product_D"],
    ]
    itemsets, _ = find_frequent_itemsets(baskets, min_support=0.2)
    rules = generate_rules(itemsets, min_confidence=0.5, min_lift=1.0)
    assert not rules.empty
    assert "antecedents" in rules.columns
    assert "consequents" in rules.columns
    assert "support" in rules.columns
    assert "confidence" in rules.columns
    assert "lift" in rules.columns
    assert "Insight" in rules.columns
    assert (rules["confidence"] >= 0.5).all()
    assert (rules["lift"] >= 1.0).all()
