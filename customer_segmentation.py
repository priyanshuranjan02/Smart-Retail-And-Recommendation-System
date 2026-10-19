"""
Smart Retail Analytics — RFM Customer Segmentation with K-Means Clustering
Segments customers by Recency, Frequency, Monetary value and visualises clusters.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use("Agg")                    # non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
OUTPUT_DIR   = "reports/figures"
DATA_DIR     = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# 1. LOAD DATA
# ──────────────────────────────────────────────

print("Loading cleaned dataset...")
df = pd.read_csv(CLEANED_FILE, parse_dates=["InvoiceDate"])
print(f"  Records: {len(df):,}   Customers: {df['CustomerID'].nunique():,}")

# ──────────────────────────────────────────────
# 2. CALCULATE RFM VALUES PER CUSTOMER
# ──────────────────────────────────────────────

# Reference date = one day after the last invoice date in the dataset
reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
print(f"  Reference date for Recency: {reference_date.date()}")

rfm = df.groupby("CustomerID").agg(
    Recency   = ("InvoiceDate", lambda x: (reference_date - x.max()).days),
    Frequency = ("InvoiceNo",   "nunique"),
    Monetary  = ("TotalAmount", "sum")
).reset_index()

rfm["Monetary"] = rfm["Monetary"].round(2)

print(f"\n{'='*60}")
print("  RFM TABLE (first 10 customers)")
print(f"{'='*60}")
print(rfm.head(10).to_string(index=False))

print(f"\n  RFM Statistics:")
print(rfm[["Recency", "Frequency", "Monetary"]].describe().round(2).to_string())

# ──────────────────────────────────────────────
# 3. NORMALIZE RFM FEATURES
# ──────────────────────────────────────────────

print("\nNormalizing RFM features (StandardScaler)...")
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
rfm_scaled_df = pd.DataFrame(rfm_scaled, columns=["Recency_sc", "Frequency_sc", "Monetary_sc"])

print("  Scaled feature stats:")
print(rfm_scaled_df.describe().round(4).to_string())

# ──────────────────────────────────────────────
# 4A. DETERMINE OPTIMAL K (ELBOW + SILHOUETTE)
# ──────────────────────────────────────────────

print("\nFinding optimal K (testing K=2..8)...")

K_range = range(2, 9)
inertias = []
silhouettes = []

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(rfm_scaled)
    inertias.append(km.inertia_)
    sil = silhouette_score(rfm_scaled, labels)
    silhouettes.append(sil)
    print(f"  K={k}  Inertia={km.inertia_:>10.2f}  Silhouette={sil:.4f}")

best_k = list(K_range)[np.argmax(silhouettes)]
print(f"\n  Best K by silhouette score: {best_k}")

# ── Plot: Elbow + Silhouette ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(K_range, inertias, "bo-", linewidth=2, markersize=8)
ax1.set_xlabel("Number of Clusters (K)", fontsize=12)
ax1.set_ylabel("Inertia (Within-Cluster SS)", fontsize=12)
ax1.set_title("Elbow Method", fontsize=14, fontweight="bold")
ax1.grid(True, alpha=0.3)

ax2.plot(K_range, silhouettes, "rs-", linewidth=2, markersize=8)
ax2.set_xlabel("Number of Clusters (K)", fontsize=12)
ax2.set_ylabel("Silhouette Score", fontsize=12)
ax2.set_title("Silhouette Analysis", fontsize=14, fontweight="bold")
ax2.grid(True, alpha=0.3)
ax2.axvline(x=best_k, color="green", linestyle="--", label=f"Best K={best_k}")
ax2.legend(fontsize=11)

plt.tight_layout()
elbow_path = os.path.join(OUTPUT_DIR, "elbow_silhouette.png")
plt.savefig(elbow_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {elbow_path}")

# ──────────────────────────────────────────────
# 4B. APPLY K-MEANS WITH OPTIMAL K
# ──────────────────────────────────────────────

# Use K=4 for interpretable business segments (or best_k if preferred)
FINAL_K = 4
print(f"\nApplying K-Means with K={FINAL_K}...")

kmeans = KMeans(n_clusters=FINAL_K, random_state=42, n_init=10, max_iter=300)
rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)
final_sil = silhouette_score(rfm_scaled, rfm["Cluster"])
print(f"  Silhouette Score: {final_sil:.4f}")

# ──────────────────────────────────────────────
# 5. LABEL CLUSTERS WITH BUSINESS NAMES
# ──────────────────────────────────────────────

# Compute cluster centres in original scale
cluster_summary = rfm.groupby("Cluster").agg(
    Count       = ("CustomerID", "count"),
    Avg_Recency = ("Recency",    "mean"),
    Avg_Freq    = ("Frequency",  "mean"),
    Avg_Monetary= ("Monetary",   "mean")
).round(2)

print(f"\n{'='*60}")
print("  CLUSTER PROFILES (before labelling)")
print(f"{'='*60}")
print(cluster_summary.to_string())

# Assign labels based on Monetary & Frequency ranking
# Sort clusters by Avg_Monetary descending
cluster_rank = cluster_summary.sort_values("Avg_Monetary", ascending=False)
label_names = ["Champions (High-Value)", "Loyal Customers", "Regular Customers", "At-Risk (Low-Value)"]

# If we have fewer labels than clusters, extend the list
while len(label_names) < FINAL_K:
    label_names.append(f"Segment {len(label_names)+1}")

label_map = {}
for i, (cluster_id, _) in enumerate(cluster_rank.iterrows()):
    label_map[cluster_id] = label_names[i]

rfm["Segment"] = rfm["Cluster"].map(label_map)

print(f"\n{'='*60}")
print("  CLUSTER LABEL ASSIGNMENTS")
print(f"{'='*60}")
for cid, label in sorted(label_map.items()):
    row = cluster_summary.loc[cid]
    print(f"  Cluster {cid} → {label}")
    print(f"    Customers: {int(row['Count'])}  |  Avg Recency: {row['Avg_Recency']:.0f} days  "
          f"|  Avg Frequency: {row['Avg_Freq']:.1f} orders  |  Avg Monetary: £{row['Avg_Monetary']:,.2f}")

# ──────────────────────────────────────────────
# 5B. RFM SCORE-BASED SEGMENTATION (Complementary)
# ──────────────────────────────────────────────

print(f"\n{'='*60}")
print("  RFM SCORE-BASED SEGMENTATION")
print(f"{'='*60}")

# Score each R, F, M from 1-5 using quantiles (5 = best)
rfm["R_Score"] = pd.qcut(rfm["Recency"],   5, labels=[5, 4, 3, 2, 1])  # lower recency = better
rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm["M_Score"] = pd.qcut(rfm["Monetary"],  5, labels=[1, 2, 3, 4, 5])

rfm["R_Score"] = rfm["R_Score"].astype(int)
rfm["F_Score"] = rfm["F_Score"].astype(int)
rfm["M_Score"] = rfm["M_Score"].astype(int)
rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

# Segment by combined RFM score
def rfm_label(score):
    if score >= 12:   return "Champions"
    elif score >= 9:  return "Potential Loyalists"
    elif score >= 6:  return "Needs Attention"
    else:             return "At Risk / Lost"

rfm["RFM_Segment"] = rfm["RFM_Score"].apply(rfm_label)

rfm_seg_summary = rfm.groupby("RFM_Segment").agg(
    Count       = ("CustomerID", "count"),
    Avg_Recency = ("Recency",    "mean"),
    Avg_Freq    = ("Frequency",  "mean"),
    Avg_Monetary= ("Monetary",   "mean"),
    Avg_Score   = ("RFM_Score",  "mean")
).round(2).sort_values("Avg_Score", ascending=False)

print(rfm_seg_summary.to_string())

# ──────────────────────────────────────────────
# 6. VISUALIZATIONS
# ──────────────────────────────────────────────

sns.set_style("whitegrid")
palette = sns.color_palette("Set2", FINAL_K)

# ── Plot 1: 2D Scatter — Frequency vs Monetary ──
fig, ax = plt.subplots(figsize=(12, 7))
for i, (seg, group) in enumerate(rfm.groupby("Segment")):
    ax.scatter(group["Frequency"], group["Monetary"],
               label=seg, alpha=0.6, s=50, edgecolors="white", linewidth=0.5)
ax.set_xlabel("Frequency (Number of Orders)", fontsize=13)
ax.set_ylabel("Monetary (Total Spend £)", fontsize=13)
ax.set_title("Customer Segments: Frequency vs Monetary", fontsize=15, fontweight="bold")
ax.legend(fontsize=11, loc="upper right")
ax.grid(True, alpha=0.3)
scatter1_path = os.path.join(OUTPUT_DIR, "segments_freq_vs_monetary.png")
plt.savefig(scatter1_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Saved: {scatter1_path}")

# ── Plot 2: 2D Scatter — Recency vs Monetary ──
fig, ax = plt.subplots(figsize=(12, 7))
for i, (seg, group) in enumerate(rfm.groupby("Segment")):
    ax.scatter(group["Recency"], group["Monetary"],
               label=seg, alpha=0.6, s=50, edgecolors="white", linewidth=0.5)
ax.set_xlabel("Recency (Days Since Last Purchase)", fontsize=13)
ax.set_ylabel("Monetary (Total Spend £)", fontsize=13)
ax.set_title("Customer Segments: Recency vs Monetary", fontsize=15, fontweight="bold")
ax.legend(fontsize=11, loc="upper right")
ax.grid(True, alpha=0.3)
scatter2_path = os.path.join(OUTPUT_DIR, "segments_recency_vs_monetary.png")
plt.savefig(scatter2_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {scatter2_path}")

# ── Plot 3: 3D Scatter — Recency vs Frequency vs Monetary ──
fig = plt.figure(figsize=(14, 9))
ax = fig.add_subplot(111, projection="3d")
for seg, group in rfm.groupby("Segment"):
    ax.scatter(group["Recency"], group["Frequency"], group["Monetary"],
               label=seg, alpha=0.6, s=40)
ax.set_xlabel("Recency (days)")
ax.set_ylabel("Frequency (orders)")
ax.set_zlabel("Monetary (£)")
ax.set_title("3D Customer Segmentation (RFM)", fontsize=14, fontweight="bold")
ax.legend(fontsize=9, loc="upper left")
scatter3d_path = os.path.join(OUTPUT_DIR, "segments_3d.png")
plt.savefig(scatter3d_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {scatter3d_path}")

# ── Plot 4: Segment Distribution Bar Chart ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

seg_counts = rfm["Segment"].value_counts()
seg_counts.plot(kind="bar", ax=ax1, color=palette, edgecolor="black", linewidth=0.5)
ax1.set_title("K-Means Segments — Customer Count", fontsize=13, fontweight="bold")
ax1.set_ylabel("Number of Customers")
ax1.set_xlabel("")
ax1.tick_params(axis="x", rotation=25)
for i, v in enumerate(seg_counts.values):
    ax1.text(i, v + 20, str(v), ha="center", fontweight="bold", fontsize=10)

rfm_seg_counts = rfm["RFM_Segment"].value_counts()
rfm_seg_counts.plot(kind="bar", ax=ax2, color=sns.color_palette("Set1", 4), edgecolor="black", linewidth=0.5)
ax2.set_title("RFM Score Segments — Customer Count", fontsize=13, fontweight="bold")
ax2.set_ylabel("Number of Customers")
ax2.set_xlabel("")
ax2.tick_params(axis="x", rotation=25)
for i, v in enumerate(rfm_seg_counts.values):
    ax2.text(i, v + 20, str(v), ha="center", fontweight="bold", fontsize=10)

plt.tight_layout()
bar_path = os.path.join(OUTPUT_DIR, "segment_distribution.png")
plt.savefig(bar_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {bar_path}")

# ── Plot 5: Heatmap — Cluster Centres ──
cluster_centres_orig = rfm.groupby("Segment")[["Recency", "Frequency", "Monetary"]].mean()
fig, ax = plt.subplots(figsize=(10, 5))
sns.heatmap(cluster_centres_orig.T, annot=True, fmt=".1f", cmap="YlOrRd",
            linewidths=1, ax=ax, cbar_kws={"label": "Value"})
ax.set_title("Cluster Centres — Average RFM Values", fontsize=14, fontweight="bold")
ax.set_ylabel("")
heatmap_path = os.path.join(OUTPUT_DIR, "cluster_heatmap.png")
plt.savefig(heatmap_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {heatmap_path}")

# ── Plot 6: Box Plots — RFM by Segment ──
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for i, col in enumerate(["Recency", "Frequency", "Monetary"]):
    sns.boxplot(data=rfm, x="Segment", y=col, ax=axes[i], palette="Set2")
    axes[i].set_title(f"{col} by Segment", fontsize=13, fontweight="bold")
    axes[i].tick_params(axis="x", rotation=25)
    axes[i].set_xlabel("")
plt.tight_layout()
box_path = os.path.join(OUTPUT_DIR, "rfm_boxplots.png")
plt.savefig(box_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: {box_path}")

# ──────────────────────────────────────────────
# 7. SAVE RESULTS
# ──────────────────────────────────────────────

output_csv = os.path.join(DATA_DIR, "customer_segments.csv")
rfm.to_csv(output_csv, index=False)
print(f"\n  Customer segments saved to: {output_csv}")

# ──────────────────────────────────────────────
# 8. FINAL SUMMARY
# ──────────────────────────────────────────────

print(f"\n{'='*60}")
print("  FINAL SUMMARY")
print(f"{'='*60}")
print(f"  Total customers segmented:  {len(rfm):,}")
print(f"  K-Means K:                  {FINAL_K}")
print(f"  Silhouette Score:           {final_sil:.4f}")
print(f"\n  K-Means Segment Breakdown:")
for seg, count in rfm["Segment"].value_counts().items():
    pct = count / len(rfm) * 100
    print(f"    {seg:30s}  {count:>5,} customers  ({pct:.1f}%)")

print(f"\n  RFM Score Segment Breakdown:")
for seg, count in rfm["RFM_Segment"].value_counts().items():
    pct = count / len(rfm) * 100
    print(f"    {seg:30s}  {count:>5,} customers  ({pct:.1f}%)")

print(f"\n  Visualizations saved to: {OUTPUT_DIR}/")
print(f"  Data exported to:        {output_csv}")
print("\nCustomer Segmentation complete.")
