"""
Smart Retail Analytics — Market Basket Analysis
Applies Apriori algorithm to discover product association rules.
"""

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# ──────────────────────────────────────────────
# 1. LOAD CLEANED DATASET
# ──────────────────────────────────────────────

print("Loading cleaned dataset...")
df = pd.read_csv("data/cleaned/online_retail_cleaned.csv")
print(f"  Records: {len(df):,}")
print(f"  Unique Invoices: {df['InvoiceNo'].nunique():,}")
print(f"  Unique Products: {df['Description'].nunique():,}")

# ──────────────────────────────────────────────
# 2. GROUP BY INVOICE → CREATE TRANSACTION BASKETS
# ──────────────────────────────────────────────
# Each basket = list of product descriptions bought in one invoice.

print("\nGrouping transactions by InvoiceNo...")
baskets = df.groupby("InvoiceNo")["Description"].apply(list).tolist()
print(f"  Total baskets (transactions): {len(baskets):,}")

# Show a sample basket
print(f"\n  Sample basket (first transaction):")
for item in baskets[0][:5]:
    print(f"    - {item}")
if len(baskets[0]) > 5:
    print(f"    ... and {len(baskets[0]) - 5} more items")

# ──────────────────────────────────────────────
# 3. ONE-HOT ENCODE THE BASKETS
# ──────────────────────────────────────────────

print("\nOne-hot encoding transactions...")
te = TransactionEncoder()
te_array = te.fit_transform(baskets)
basket_df = pd.DataFrame(te_array, columns=te.columns_)

print(f"  Basket matrix shape: {basket_df.shape}")
print(f"  (rows = transactions, columns = unique products)")

# ──────────────────────────────────────────────
# 4. APPLY APRIORI ALGORITHM
# ──────────────────────────────────────────────
# min_support = 0.02 means the itemset must appear in at least 2% of transactions.
# Adjust this threshold based on dataset characteristics:
#   - Too high  → very few rules (misses niche associations)
#   - Too low   → too many rules (noise, slow computation)

MIN_SUPPORT = 0.02

print(f"\nRunning Apriori with min_support = {MIN_SUPPORT}...")
frequent_itemsets = apriori(
    basket_df,
    min_support=MIN_SUPPORT,
    use_colnames=True,
    max_len=3          # limit to pairs and triplets for interpretability
)

print(f"  Frequent itemsets found: {len(frequent_itemsets)}")

# Show top frequent itemsets
print("\n  Top 10 Frequent Itemsets by Support:")
top_itemsets = frequent_itemsets.sort_values("support", ascending=False).head(10)
for _, row in top_itemsets.iterrows():
    items = ", ".join(list(row["itemsets"]))
    print(f"    Support: {row['support']:.4f}  →  {items}")

# ──────────────────────────────────────────────
# 5. GENERATE ASSOCIATION RULES
# ──────────────────────────────────────────────
# metric="lift" with min_threshold=1.0 ensures rules are better than random chance.

print("\nGenerating association rules (min_confidence=0.3, min_lift=1.0)...")
rules = association_rules(
    frequent_itemsets,
    metric="lift",
    min_threshold=1.0,
    num_itemsets=len(frequent_itemsets)
)

# Filter for meaningful rules
rules = rules[rules["confidence"] >= 0.3]
print(f"  Association rules found: {len(rules)}")

# ──────────────────────────────────────────────
# 6. FORMAT RULES AS BUSINESS INSIGHTS
# ──────────────────────────────────────────────

def format_rule(row):
    """Convert a rule row into a human-readable insight."""
    antecedent = ", ".join(list(row["antecedents"]))
    consequent = ", ".join(list(row["consequents"]))
    return f'If a customer buys [{antecedent}], they are likely to buy [{consequent}]'

rules["Insight"] = rules.apply(format_rule, axis=1)

# ──────────────────────────────────────────────
# 7. DISPLAY TOP 10 RULES BY CONFIDENCE
# ──────────────────────────────────────────────

print("\n" + "=" * 80)
print("  TOP 10 ASSOCIATION RULES — SORTED BY CONFIDENCE")
print("=" * 80)

top_confidence = rules.sort_values("confidence", ascending=False).head(10)
display_cols = ["Insight", "support", "confidence", "lift"]

for i, (_, row) in enumerate(top_confidence.iterrows(), 1):
    print(f"\n  Rule {i}:")
    print(f"    {row['Insight']}")
    print(f"    Support:    {row['support']:.4f}  "
          f"({row['support'] * 100:.2f}% of transactions)")
    print(f"    Confidence: {row['confidence']:.4f}  "
          f"({row['confidence'] * 100:.1f}% chance)")
    print(f"    Lift:       {row['lift']:.4f}  "
          f"({'strong' if row['lift'] > 3 else 'moderate' if row['lift'] > 1.5 else 'weak'} association)")

# ──────────────────────────────────────────────
# 8. DISPLAY TOP 10 RULES BY LIFT
# ──────────────────────────────────────────────

print("\n\n" + "=" * 80)
print("  TOP 10 ASSOCIATION RULES — SORTED BY LIFT")
print("=" * 80)

top_lift = rules.sort_values("lift", ascending=False).head(10)

for i, (_, row) in enumerate(top_lift.iterrows(), 1):
    print(f"\n  Rule {i}:")
    print(f"    {row['Insight']}")
    print(f"    Support:    {row['support']:.4f}  "
          f"({row['support'] * 100:.2f}% of transactions)")
    print(f"    Confidence: {row['confidence']:.4f}  "
          f"({row['confidence'] * 100:.1f}% chance)")
    print(f"    Lift:       {row['lift']:.4f}  "
          f"({'strong' if row['lift'] > 3 else 'moderate' if row['lift'] > 1.5 else 'weak'} association)")

# ──────────────────────────────────────────────
# 9. SAVE FULL RULES TABLE TO CSV
# ──────────────────────────────────────────────

# Clean up for CSV export
rules_export = rules.copy()
rules_export["antecedents"] = rules_export["antecedents"].apply(lambda x: ", ".join(list(x)))
rules_export["consequents"] = rules_export["consequents"].apply(lambda x: ", ".join(list(x)))

output_file = "data/processed/association_rules.csv"
rules_export.to_csv(output_file, index=False)
print(f"\n\nFull rules table saved to: {output_file}")
print(f"Total rules exported: {len(rules_export)}")

# ──────────────────────────────────────────────
# 10. SUMMARY STATISTICS
# ──────────────────────────────────────────────

print("\n" + "=" * 80)
print("  SUMMARY")
print("=" * 80)
print(f"  Total transactions analysed:  {len(baskets):,}")
print(f"  Unique products:              {basket_df.shape[1]:,}")
print(f"  Min support threshold:        {MIN_SUPPORT}")
print(f"  Frequent itemsets found:      {len(frequent_itemsets)}")
print(f"  Association rules generated:  {len(rules)}")
print(f"  Avg confidence:               {rules['confidence'].mean():.4f}")
print(f"  Avg lift:                     {rules['lift'].mean():.4f}")
print(f"  Max lift:                     {rules['lift'].max():.4f}")
print(f"\n  Output file: {output_file}")
print("\nMarket Basket Analysis complete.")
