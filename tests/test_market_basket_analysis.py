"""
Unit tests for Market Basket Analysis and Apriori association rules.
"""

import pandas as pd
from market_basket_analysis import (
    build_transaction_baskets,
    find_frequent_itemsets,
    format_itemset,
    generate_rules,
    run_market_basket_analysis,
)


def test_format_itemset_canonical():
    """Verify canonical formatting produces identical sorted strings regardless of item order."""
    assert format_itemset(["Banana", "Apple", "Cherry"]) == "Apple, Banana, Cherry"
    assert format_itemset(frozenset(["Cherry", "Banana", "Apple"])) == "Apple, Banana, Cherry"
    assert format_itemset([" Single Item "]) == "Single Item"
    assert format_itemset("Already Formatted String") == "Already Formatted String"
    assert format_itemset([]) == ""
    assert format_itemset(set()) == ""
    assert format_itemset(None) == ""


def test_build_transaction_baskets(sample_cleaned_df):
    """Verify clean line items are grouped into unique product name lists per InvoiceNo."""
    baskets = build_transaction_baskets(sample_cleaned_df)
    assert len(baskets) == 5  # 5 distinct invoices in fixture
    # Invoice 500001 has Product Alpha and Product Beta
    assert any(set(["Product Alpha", "Product Beta"]).issubset(set(b)) for b in baskets)
    # Verify items within each basket are sorted and deduplicated
    for b in baskets:
        assert b == sorted(set(b))


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


def test_mba_outputs_byte_identical_reproducibility(tmp_path):
    """Verify consecutive MBA runs on identical data produce byte-for-byte identical output files."""
    cleaned_csv = tmp_path / "cleaned_data.csv"
    data = {
        "InvoiceNo": ["101", "101", "102", "102", "102", "103", "103", "104", "104", "105", "105"],
        "Description": ["Bread", "Milk", "Milk", "Butter", "Bread", "Bread", "Milk", "Butter", "Eggs", "Bread", "Milk"],
        "Quantity": [1, 2, 1, 1, 3, 1, 2, 1, 1, 2, 1],
        "UnitPrice": [1.5, 2.0, 2.0, 3.0, 1.5, 1.5, 2.0, 3.0, 2.5, 1.5, 2.0],
        "CustomerID": [10, 10, 20, 20, 20, 30, 30, 40, 40, 50, 50],
        "InvoiceDate": ["2023-01-01"] * 11,
        "Country": ["United Kingdom"] * 11
    }
    pd.DataFrame(data).to_csv(cleaned_csv, index=False)

    dir_run1 = tmp_path / "run1"
    dir_run2 = tmp_path / "run2"

    run_market_basket_analysis(
        cleaned_file=str(cleaned_csv),
        min_support=0.1,
        min_confidence=0.1,
        min_lift=0.5,
        output_dir=str(dir_run1)
    )

    run_market_basket_analysis(
        cleaned_file=str(cleaned_csv),
        min_support=0.1,
        min_confidence=0.1,
        min_lift=0.5,
        output_dir=str(dir_run2)
    )

    expected_files = [
        "frequent_itemsets.csv",
        "association_rules.csv",
        "mba_summary.json",
        "mba_results.txt"
    ]
    for filename in expected_files:
        f1 = dir_run1 / filename
        f2 = dir_run2 / filename
        assert f1.exists(), f"File {filename} was not generated in run 1"
        assert f2.exists(), f"File {filename} was not generated in run 2"
        assert f1.read_bytes() == f2.read_bytes(), f"File {filename} is not byte-identical between runs"

