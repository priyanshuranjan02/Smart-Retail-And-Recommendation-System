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


def format_itemset(itemset) -> str:
    """
    Convert an iterable, frozenset, or string representing an itemset into
    a canonical, alphabetically sorted comma-separated string of product names.
    """
    if isinstance(itemset, str):
        return itemset
    if itemset is None:
        return ""
    return ", ".join(sorted(str(item).strip() for item in itemset))


def build_transaction_baskets(df: pd.DataFrame) -> list[list[str]]:
    """Group clean line items by InvoiceNo into sorted, unique product name baskets."""
    # Clean description strings (strip leading/trailing whitespaces)
    df_clean = df.dropna(subset=["Description"]).copy()
    df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
    df_clean = df_clean[df_clean["Description"] != ""]
    baskets = (
        df_clean.groupby("InvoiceNo", sort=True)["Description"]
        .apply(lambda s: sorted(set(s)))
        .tolist()
    )
    return baskets


def find_frequent_itemsets(
    baskets: list[list[str]],
    min_support: float = MIN_SUPPORT,
    max_len: int = MAX_LEN
) -> tuple[pd.DataFrame, pd.DataFrame]:
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
    if frequent_itemsets.empty:
        frequent_itemsets["length"] = pd.Series(dtype=int)
        return frequent_itemsets, basket_df

    frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(len)
    frequent_itemsets["_canonical_name"] = frequent_itemsets["itemsets"].apply(format_itemset)
    frequent_itemsets = (
        frequent_itemsets.sort_values(
            by=["length", "_canonical_name"],
            ascending=[True, True]
        )
        .drop(columns=["_canonical_name"])
        .reset_index(drop=True)
    )
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

    # Create business insight readable string using canonical formatting
    def format_insight(row):
        ante = format_itemset(row["antecedents"])
        cons = format_itemset(row["consequents"])
        return f"If customer buys [{ante}], they are likely to also buy [{cons}]"

    rules["Insight"] = rules.apply(format_insight, axis=1)

    # Sort rules deterministically using existing ranking metrics and canonical tie-breakers
    rules["_ante_str"] = rules["antecedents"].apply(format_itemset)
    rules["_cons_str"] = rules["consequents"].apply(format_itemset)
    rules = (
        rules.sort_values(
            by=["confidence", "lift", "support", "_ante_str", "_cons_str"],
            ascending=[False, False, False, True, True]
        )
        .drop(columns=["_ante_str", "_cons_str"])
        .reset_index(drop=True)
    )

    return rules


def run_market_basket_analysis(
    cleaned_file: str = CLEANED_FILE,
    min_support: float = MIN_SUPPORT,
    min_confidence: float = MIN_CONFIDENCE,
    min_lift: float = MIN_LIFT,
    output_dir: str = DATA_DIR
) -> dict:
    """End-to-end execution of Market Basket Analysis."""
    os.makedirs(output_dir, exist_ok=True)
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
    fi_export["itemsets"] = fi_export["itemsets"].apply(format_itemset)
    fi_export = (
        fi_export.sort_values(by=["length", "itemsets"], ascending=[True, True])
        .reindex(columns=["support", "itemsets", "length"])
        .reset_index(drop=True)
    )
    fi_export_path = os.path.join(output_dir, "frequent_itemsets.csv")
    fi_export.to_csv(fi_export_path, index=False)
    print(f"  Frequent itemsets exported to: {fi_export_path}")

    print(f"\nGenerating association rules (min_confidence={min_confidence}, min_lift={min_lift})...")
    rules = generate_rules(frequent_itemsets, min_confidence=min_confidence, min_lift=min_lift)
    print(f"  Association rules generated: {len(rules)}")

    # Format rules for export
    rules_export = rules.copy()
    rules_export["antecedents"] = rules_export["antecedents"].apply(format_itemset)
    rules_export["consequents"] = rules_export["consequents"].apply(format_itemset)
    rules_export = rules_export.sort_values(
        by=["confidence", "lift", "support", "antecedents", "consequents"],
        ascending=[False, False, False, True, True]
    ).reset_index(drop=True)
    rules_csv_path = os.path.join(output_dir, "association_rules.csv")
    rules_export.to_csv(rules_csv_path, index=False)
    print(f"  Full rules exported to: {rules_csv_path}")

    # Top sample rule for documentation
    top_rule_sample = {}
    if not rules.empty:
        top_rule = rules.iloc[0]
        ante_str = format_itemset(top_rule["antecedents"])
        cons_str = format_itemset(top_rule["consequents"])
        top_rule_sample = {
            "antecedent": ante_str,
            "consequent": cons_str,
            "support": float(round(top_rule["support"], 4)),
            "confidence": float(round(top_rule["confidence"], 4)),
            "lift": float(round(top_rule["lift"], 4)),
            "explanation": (
                f"Rule: [{ante_str}] -> [{cons_str}]. "
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

    summary_json_path = os.path.join(output_dir, "mba_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary metadata saved to: {summary_json_path}")

    # Text report
    txt_path = os.path.join(output_dir, "mba_results.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Total rules: {len(rules)}\n")
        f.write(f"Avg confidence: {summary['avg_confidence']:.4f}\n")
        f.write(f"Avg lift: {summary['avg_lift']:.4f}\n")
        f.write(f"Max lift: {summary['max_lift']:.4f}\n\n")
        f.write("TOP 10 BY CONFIDENCE\n")
        top_conf = rules.head(10)
        for i, (_, r) in enumerate(top_conf.iterrows(), 1):
            ante = format_itemset(r["antecedents"])
            cons = format_itemset(r["consequents"])
            f.write(f"{i}. [{ante}] -> [{cons}]\n")
            f.write(f"   Support={r['support']:.4f} Confidence={r['confidence']:.4f} Lift={r['lift']:.4f}\n")
        f.write("\nTOP 10 BY LIFT\n")
        rules_temp = rules.copy()
        rules_temp["_ante_str"] = rules_temp["antecedents"].apply(format_itemset)
        rules_temp["_cons_str"] = rules_temp["consequents"].apply(format_itemset)
        top_lft = rules_temp.sort_values(
            by=["lift", "confidence", "support", "_ante_str", "_cons_str"],
            ascending=[False, False, False, True, True]
        ).head(10)
        for i, (_, r) in enumerate(top_lft.iterrows(), 1):
            ante = format_itemset(r["antecedents"])
            cons = format_itemset(r["consequents"])
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
    parser.add_argument("--output-dir", default=DATA_DIR)

    args = parser.parse_args()
    run_market_basket_analysis(
        cleaned_file=args.cleaned_file,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
