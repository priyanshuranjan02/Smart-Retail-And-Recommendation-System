"""
Smart Retail Analytics — Market Basket Analysis
Applies the Apriori algorithm to discover actionable product association rules.
Calculates Support, Confidence, Lift, and generates business cross-sell recommendations.
"""

import os
import json
import argparse
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
DATA_DIR     = "data/processed"
MIN_SUPPORT  = 0.02
MIN_CONFIDENCE = 0.30
MIN_LIFT     = 1.0
MAX_LEN      = 3

os.makedirs(DATA_DIR, exist_ok=True)


def build_transaction_baskets(df: pd.DataFrame) -> list[list[str]]:
    """Group clean line items by InvoiceNo into product name baskets."""
    # Clean description strings (strip leading/trailing whitespaces)
    df_clean = df.dropna(subset=["Description"]).copy()
    df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
    baskets = df_clean.groupby("InvoiceNo")["Description"].apply(lambda s: list(set(s))).tolist()
    return baskets


def find_frequent_itemsets(baskets: list[list[str]], min_support: float = MIN_SUPPORT, max_len: int = MAX_LEN) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One-hot encode baskets and run Apriori algorithm to discover frequent itemsets."""
    te = TransactionEncoder()
    te_ary = te.fit_transform(baskets)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)

    frequent_itemsets = apriori(
        basket_df,
        min_support=min_support,
        use_colnames=True,
        max_len=max_len
    )
    frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(len)
    return frequent_itemsets, basket_df


def generate_rules(
    frequent_itemsets: pd.DataFrame,
    min_confidence: float = MIN_CONFIDENCE,
    min_lift: float = MIN_LIFT
) -> pd.DataFrame:
    """
    Generate association rules using Apriori frequent itemsets:
      - Association rules generated with metric='lift' and min_threshold=min_lift
      - Then filtered by confidence >= min_confidence
    """
    if frequent_itemsets.empty:
        return pd.DataFrame()

    rules = association_rules(
        frequent_itemsets,
        metric="lift",
        min_threshold=min_lift,
        num_itemsets=len(frequent_itemsets)
    )

    rules = rules[rules["confidence"] >= min_confidence].copy()

    if rules.empty:
        rules["Insight"] = pd.Series(dtype=str)
        return rules

    # Create business insight readable string
    def format_insight(row):
        ante = ", ".join(list(row["antecedents"]))
        cons = ", ".join(list(row["consequents"]))
        return f"If customer buys [{ante}], they are likely to also buy [{cons}]"

    rules["Insight"] = rules.apply(format_insight, axis=1)
    return rules


def run_market_basket_analysis(
    cleaned_file: str = CLEANED_FILE,
    min_support: float = MIN_SUPPORT,
    min_confidence: float = MIN_CONFIDENCE,
    min_lift: float = MIN_LIFT
) -> dict:
    """End-to-end execution of Market Basket Analysis."""
    print("Loading cleaned dataset...")
    df = pd.read_csv(cleaned_file)
    print(f"  Records: {len(df):,}")
    print(f"  Unique Invoices: {df['InvoiceNo'].nunique():,}")
    print(f"  Unique Products: {df['Description'].nunique():,}")

    baskets = build_transaction_baskets(df)
    total_transactions = len(baskets)
    print(f"\nGrouped transactions into {total_transactions:,} distinct shopping baskets.")

    print(f"\nRunning Apriori with min_support={min_support} (>= {int(min_support * total_transactions)} transactions)...")
    frequent_itemsets, basket_df = find_frequent_itemsets(baskets, min_support=min_support)
    print(f"  Frequent itemsets found: {len(frequent_itemsets)}")

    # Save frequent itemsets CSV
    fi_export = frequent_itemsets.copy()
    fi_export["itemsets"] = fi_export["itemsets"].apply(lambda x: ", ".join(list(x)))
    fi_export_path = os.path.join(DATA_DIR, "frequent_itemsets.csv")
    fi_export.to_csv(fi_export_path, index=False)
    print(f"  Frequent itemsets exported to: {fi_export_path}")

    print(f"\nGenerating association rules (min_confidence={min_confidence}, min_lift={min_lift})...")
    rules = generate_rules(frequent_itemsets, min_confidence=min_confidence, min_lift=min_lift)
    print(f"  Association rules generated: {len(rules)}")

    # Format rules for export
    rules_export = rules.copy()
    rules_export["antecedents"] = rules_export["antecedents"].apply(lambda x: ", ".join(list(x)))
    rules_export["consequents"] = rules_export["consequents"].apply(lambda x: ", ".join(list(x)))
    rules_csv_path = os.path.join(DATA_DIR, "association_rules.csv")
    rules_export.to_csv(rules_csv_path, index=False)
    print(f"  Full rules exported to: {rules_csv_path}")

    # Top sample rule for documentation
    top_rule_sample = {}
    if not rules.empty:
        top_rule = rules.sort_values("confidence", ascending=False).iloc[0]
        top_rule_sample = {
            "antecedent": ", ".join(list(top_rule["antecedents"])),
            "consequent": ", ".join(list(top_rule["consequents"])),
            "support": float(round(top_rule["support"], 4)),
            "confidence": float(round(top_rule["confidence"], 4)),
            "lift": float(round(top_rule["lift"], 4)),
            "explanation": (
                f"Rule: [{', '.join(list(top_rule['antecedents']))}] -> [{', '.join(list(top_rule['consequents']))}]. "
                f"Support = {top_rule['support']:.2%} of all {total_transactions:,} orders contained both items. "
                f"Confidence = {top_rule['confidence']:.1%} of customers who bought the antecedent also bought the consequent. "
                f"Lift = {top_rule['lift']:.2f}x means the pair occurs {top_rule['lift']:.2f} times more frequently than if purchases were independent."
            )
        }

    # Summary JSON payload
    summary = {
        "total_transactions": total_transactions,
        "unique_products": int(basket_df.shape[1]),
        "min_support_threshold": min_support,
        "min_confidence_threshold": min_confidence,
        "min_lift_threshold": min_lift,
        "frequent_itemsets_count": len(frequent_itemsets),
        "rules_count": len(rules),
        "avg_confidence": float(round(rules["confidence"].mean(), 4)) if not rules.empty else 0.0,
        "avg_lift": float(round(rules["lift"].mean(), 4)) if not rules.empty else 0.0,
        "max_lift": float(round(rules["lift"].max(), 4)) if not rules.empty else 0.0,
        "top_rule_sample": top_rule_sample,
        "definitions": {
            "support": "Frequency of itemset co-occurrence across all transactions (P(A and B)).",
            "confidence": "Conditional probability that consequent B is bought given antecedent A (P(B|A)).",
            "lift": "Ratio of observed co-occurrence to expected co-occurrence under statistical independence (P(B|A) / P(B)). Lift > 1 indicates positive association.",
            "caveat": "Association rules show statistical correlation and co-purchase affinity, not direct causal proof or guaranteed future purchases."
        }
    }

    summary_json_path = os.path.join(DATA_DIR, "mba_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary metadata saved to: {summary_json_path}")

    # Text report
    txt_path = os.path.join(DATA_DIR, "mba_results.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Total rules: {len(rules)}\n")
        f.write(f"Avg confidence: {summary['avg_confidence']:.4f}\n")
        f.write(f"Avg lift: {summary['avg_lift']:.4f}\n")
        f.write(f"Max lift: {summary['max_lift']:.4f}\n\n")
        f.write("TOP 10 BY CONFIDENCE\n")
        top_conf = rules.sort_values("confidence", ascending=False).head(10)
        for i, (_, r) in enumerate(top_conf.iterrows(), 1):
            ante = ", ".join(list(r["antecedents"]))
            cons = ", ".join(list(r["consequents"]))
            f.write(f"{i}. [{ante}] -> [{cons}]\n")
            f.write(f"   Support={r['support']:.4f} Confidence={r['confidence']:.4f} Lift={r['lift']:.4f}\n")
        f.write("\nTOP 10 BY LIFT\n")
        top_lft = rules.sort_values("lift", ascending=False).head(10)
        for i, (_, r) in enumerate(top_lft.iterrows(), 1):
            ante = ", ".join(list(r["antecedents"]))
            cons = ", ".join(list(r["consequents"]))
            f.write(f"{i}. [{ante}] -> [{cons}]\n")
            f.write(f"   Support={r['support']:.4f} Confidence={r['confidence']:.4f} Lift={r['lift']:.4f}\n")
    print(f"  Text report written to: {txt_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Retail Market Basket Analysis")
    parser.add_argument("--cleaned-file", default=CLEANED_FILE)
    parser.add_argument("--min-support", type=float, default=MIN_SUPPORT)
    parser.add_argument("--min-confidence", type=float, default=MIN_CONFIDENCE)
    parser.add_argument("--min-lift", type=float, default=MIN_LIFT)

    args = parser.parse_args()
    run_market_basket_analysis(
        cleaned_file=args.cleaned_file,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift
    )


if __name__ == "__main__":
    main()
