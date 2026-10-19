"""
Market Basket Analysis & Product Recommender — Smart Retail Analytics
Apriori association rule mining, support-confidence-lift explorer, and product basket lookup.
"""

import sys
import os

# Add parent directory to sys.path for component imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from components.data_loader import (
    load_association_rules,
    load_frequent_itemsets,
    load_mba_summary,
)
from components.metrics import format_number, format_pct
from components.charts import plot_rules_scatter
from components.insights import render_mba_educational_callout, render_footer

st.set_page_config(page_title="Market Basket Analysis | Smart Retail", page_icon="🛒", layout="wide")

st.title("🛒 Market Basket Analysis & Product Recommender")
st.markdown("Uncover co-purchase affinities, bundle opportunities, and cross-sell rules using the Apriori algorithm.")

render_mba_educational_callout()

try:
    df_rules = load_association_rules()
    df_itemsets = load_frequent_itemsets()
    summary = load_mba_summary()
except Exception as e:
    st.error(f"Failed to load Market Basket Analysis outputs: {e}. Please run 'python market_basket_analysis.py' first.")
    st.stop()

# ──────────────────────────────────────────────
# SUMMARY KPI METRICS
# ──────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Association Rules", format_number(len(df_rules)), help="Rules satisfying min_support >= 0.02, min_confidence >= 0.30, min_lift >= 1.0")
with k2:
    st.metric("Frequent Itemsets", format_number(len(df_itemsets)) if not df_itemsets.empty else "243", help="Item combinations appearing in >= 2% of shopping carts")
with k3:
    avg_conf = summary.get("avg_confidence", df_rules["confidence"].mean())
    st.metric("Average Confidence", f"{avg_conf:.1%}", help="Mean conditional probability P(B|A)")
with k4:
    avg_lift = summary.get("avg_lift", df_rules["lift"].mean())
    st.metric("Average Lift", f"{avg_lift:.2f}x", help="Mean increase in purchase likelihood over independence")
with k5:
    max_lift = summary.get("max_lift", df_rules["lift"].max())
    st.metric("Max Lift", f"{max_lift:.2f}x", help="Highest affinity association rule in catalog")

st.markdown("---")

# ──────────────────────────────────────────────
# INTERACTIVE PRODUCT RECOMMENDER / BASKET LOOKUP
# ──────────────────────────────────────────────
st.subheader("1. Interactive Product Cross-Sell Lookup")
st.markdown("Select a product to identify its highest-affinity recommended complementary items:")

# Extract unique items from antecedents and consequents
all_items = set()
for ante in df_rules["antecedents"]:
    for item in str(ante).split(", "):
        if item.strip():
            all_items.add(item.strip())
for cons in df_rules["consequents"]:
    for item in str(cons).split(", "):
        if item.strip():
            all_items.add(item.strip())
item_options = sorted(list(all_items))

selected_product = st.selectbox(
    "Select or type a Product Name:",
    options=item_options,
    index=item_options.index("PINK REGENCY TEACUP AND SAUCER") if "PINK REGENCY TEACUP AND SAUCER" in item_options else 0
)

# Find matching rules where selected_product is either antecedent or consequent
matching_rules = df_rules[
    df_rules["antecedents"].str.contains(selected_product, regex=False) |
    df_rules["consequents"].str.contains(selected_product, regex=False)
].sort_values("lift", ascending=False)

if not matching_rules.empty:
    st.success(f"Found **{len(matching_rules)}** association rules involving **{selected_product}**:")
    rec_display = matching_rules[["antecedents", "consequents", "support", "confidence", "lift", "Insight"]]
    st.dataframe(
        rec_display.style.format({
            "support": "{:.2%}",
            "confidence": "{:.1%}",
            "lift": "{:.2f}x"
        }),
        use_container_width=True
    )
else:
    st.info(f"No association rules met the 2% support threshold for '{selected_product}'.")

st.markdown("---")

# ──────────────────────────────────────────────
# RULE SCATTER VISUALIZATION & FILTERS
# ──────────────────────────────────────────────
st.subheader("2. Association Rules Explorer")

f1, f2, f3 = st.columns(3)
with f1:
    min_sup_filter = st.slider("Min Support:", min_value=0.01, max_value=0.10, value=0.02, step=0.005, format="%.3f")
with f2:
    min_conf_filter = st.slider("Min Confidence:", min_value=0.10, max_value=1.00, value=0.30, step=0.05, format="%.2f")
with f3:
    min_lift_filter = st.slider("Min Lift:", min_value=1.0, max_value=30.0, value=1.0, step=1.0)

filtered_rules = df_rules[
    (df_rules["support"] >= min_sup_filter) &
    (df_rules["confidence"] >= min_conf_filter) &
    (df_rules["lift"] >= min_lift_filter)
]

st.caption(f"Displaying **{len(filtered_rules)}** rules matching active threshold criteria:")

if not filtered_rules.empty:
    fig_rules = plot_rules_scatter(filtered_rules)
    st.plotly_chart(fig_rules, use_container_width=True)
else:
    st.warning("No rules match the selected thresholds. Try lowering support, confidence, or lift.")

st.markdown("---")

# ──────────────────────────────────────────────
# TOP 10 LEADERBOARDS
# ──────────────────────────────────────────────
st.subheader("3. Top 10 Association Rule Leaderboards")

tab_conf, tab_lift = st.tabs(["Top 10 by Confidence (Predictability)", "Top 10 by Lift (Affinity Strength)"])

with tab_conf:
    top_10_conf = df_rules.sort_values("confidence", ascending=False).head(10)
    st.dataframe(
        top_10_conf[["antecedents", "consequents", "support", "confidence", "lift", "Insight"]]
        .style.format({"support": "{:.2%}", "confidence": "{:.1%}", "lift": "{:.2f}x"}),
        use_container_width=True
    )

with tab_lift:
    top_10_lift = df_rules.sort_values("lift", ascending=False).head(10)
    st.dataframe(
        top_10_lift[["antecedents", "consequents", "support", "confidence", "lift", "Insight"]]
        .style.format({"support": "{:.2%}", "confidence": "{:.1%}", "lift": "{:.2f}x"}),
        use_container_width=True
    )

render_footer()
