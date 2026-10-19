"""
Smart Retail Analytics — Data Cleaning Pipeline
Dataset: UCI Online Retail (Online Retail.xlsx)
"""

import os
import pandas as pd
import numpy as np
import urllib.request

# ──────────────────────────────────────────────
# 1. DOWNLOAD & LOAD THE DATASET
# ──────────────────────────────────────────────

RAW_DIR = "data/raw"
CLEANED_DIR = "data/cleaned"
RAW_FILE = os.path.join(RAW_DIR, "OnlineRetail.xlsx")
CLEANED_FILE = os.path.join(CLEANED_DIR, "online_retail_cleaned.csv")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)

# Download if not already present
if not os.path.exists(RAW_FILE):
    print("Downloading UCI Online Retail dataset...")
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
    urllib.request.urlretrieve(url, RAW_FILE)
    print("Download complete.")
else:
    print("Dataset already exists. Skipping download.")

# Load the Excel file
print("Loading dataset...")
df = pd.read_excel(RAW_FILE, engine="openpyxl")
print(f"Raw dataset shape: {df.shape}")
print(f"Columns: {list(df.columns)}\n")

# ──────────────────────────────────────────────
# 2. INSPECT THE DATA — NULLS, DUPLICATES, INVALID RECORDS
# ──────────────────────────────────────────────

print("=" * 60)
print("DATA QUALITY REPORT (Before Cleaning)")
print("=" * 60)

# Null values per column
print("\n--- Null Values ---")
null_counts = df.isnull().sum()
null_pct = (df.isnull().sum() / len(df) * 100).round(2)
null_report = pd.DataFrame({"NullCount": null_counts, "NullPercent": null_pct})
print(null_report[null_report["NullCount"] > 0])

# Duplicate rows
dup_count = df.duplicated().sum()
print(f"\n--- Duplicate Rows: {dup_count} ({dup_count / len(df) * 100:.2f}%) ---")

# Negative quantities (potential returns / errors)
neg_qty = (df["Quantity"] <= 0).sum()
print(f"\n--- Rows with Quantity <= 0: {neg_qty} ---")

# Zero or negative unit prices
bad_price = (df["UnitPrice"] <= 0).sum()
print(f"--- Rows with UnitPrice <= 0: {bad_price} ---")

# Cancelled invoices (InvoiceNo starts with 'C')
cancelled = df["InvoiceNo"].astype(str).str.startswith("C").sum()
print(f"--- Cancelled Invoices (starts with 'C'): {cancelled} ---\n")

# ──────────────────────────────────────────────
# 3. REMOVE CANCELLED INVOICES & NEGATIVE QUANTITIES
# ──────────────────────────────────────────────

print("Removing cancelled invoices...")
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
print(f"  Shape after removing cancellations: {df.shape}")

print("Removing rows with Quantity <= 0...")
df = df[df["Quantity"] > 0]
print(f"  Shape after removing non-positive quantities: {df.shape}")

print("Removing rows with UnitPrice <= 0...")
df = df[df["UnitPrice"] > 0]
print(f"  Shape after removing non-positive prices: {df.shape}")

# ──────────────────────────────────────────────
# 4. HANDLE MISSING CUSTOMER IDs
# ──────────────────────────────────────────────

missing_cid_before = df["CustomerID"].isnull().sum()
print(f"\nMissing CustomerID values: {missing_cid_before} ({missing_cid_before / len(df) * 100:.2f}%)")

# Strategy: Drop rows with missing CustomerID
# Rationale: CustomerID is essential for segmentation, recommendations, and churn.
#            Imputation is not meaningful for a unique identifier.
df = df.dropna(subset=["CustomerID"])
print(f"  Shape after dropping missing CustomerID: {df.shape}")

# Convert CustomerID to integer (it was float due to NaN presence)
df["CustomerID"] = df["CustomerID"].astype(int)

# ──────────────────────────────────────────────
# 5. REMOVE DUPLICATE ROWS
# ──────────────────────────────────────────────

dup_before = df.duplicated().sum()
print(f"\nDuplicate rows remaining: {dup_before}")
df = df.drop_duplicates()
print(f"  Shape after removing duplicates: {df.shape}")

# ──────────────────────────────────────────────
# 6. CREATE TotalAmount COLUMN
# ──────────────────────────────────────────────

df["TotalAmount"] = (df["Quantity"] * df["UnitPrice"]).round(2)
print(f"\nTotalAmount column created.")
print(f"  Min: {df['TotalAmount'].min()}")
print(f"  Max: {df['TotalAmount'].max()}")
print(f"  Mean: {df['TotalAmount'].mean():.2f}")

# ──────────────────────────────────────────────
# 7. FINAL VALIDATION
# ──────────────────────────────────────────────

print("\n" + "=" * 60)
print("DATA QUALITY REPORT (After Cleaning)")
print("=" * 60)
print(f"Final shape: {df.shape}")
print(f"Remaining nulls:\n{df.isnull().sum()}")
print(f"Remaining duplicates: {df.duplicated().sum()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nSample rows:")
print(df.head(10).to_string(index=False))

# ──────────────────────────────────────────────
# 8. SAVE CLEANED DATASET
# ──────────────────────────────────────────────

df.to_csv(CLEANED_FILE, index=False)
print(f"\nCleaned dataset saved to: {CLEANED_FILE}")
print(f"Final record count: {len(df):,}")
print("Data cleaning pipeline complete.")
