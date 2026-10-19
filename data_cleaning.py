"""
Smart Retail Analytics — Data Cleaning Pipeline
Dataset: UCI Online Retail (Online Retail.xlsx)
"""

import os
import urllib.request
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

RAW_DIR = "data/raw"
CLEANED_DIR = "data/cleaned"
RAW_FILE = os.path.join(RAW_DIR, "OnlineRetail.xlsx")
CLEANED_FILE = os.path.join(CLEANED_DIR, "online_retail_cleaned.csv")
DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"


def acquire_raw_dataset(raw_file: str = RAW_FILE, url: str = DATASET_URL) -> str:
    """Ensure the raw dataset exists locally, downloading if necessary."""
    os.makedirs(os.path.dirname(raw_file), exist_ok=True)
    if not os.path.exists(raw_file):
        print(f"Downloading UCI Online Retail dataset from {url}...")
        try:
            opener = urllib.request.build_opener()
            opener.addheaders = [("User-Agent", "SmartRetailAnalytics/1.0")]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, raw_file)
            print("Download complete.")
        except Exception as e:
            raise RuntimeError(
                f"Failed to download dataset from {url}: {e}\n"
                f"Please manually place 'OnlineRetail.xlsx' into '{os.path.dirname(raw_file)}/'."
            ) from e
    else:
        print("Raw dataset already exists. Skipping download.")
    return raw_file


def clean_dataset(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Cleans raw retail transaction records according to documented business rules:
      1. Remove cancelled invoices (InvoiceNo starts with 'C')
      2. Filter out non-positive quantities (<= 0)
      3. Filter out non-positive unit prices (<= 0)
      4. Drop records with missing CustomerID (imputation invalid for identity)
      5. Convert CustomerID to integer
      6. Remove duplicate rows
      7. Calculate TotalAmount = round(Quantity * UnitPrice, 2)
      8. Parse InvoiceDate to datetime
    """
    # Pre-cleaning quality audit
    stats = {
        "raw_rows": len(df_raw),
        "raw_cols": len(df_raw.columns),
        "cancelled_rows": int(df_raw["InvoiceNo"].astype(str).str.startswith("C").sum()),
        "non_positive_qty_rows": int((df_raw["Quantity"] <= 0).sum()),
        "non_positive_price_rows": int((df_raw["UnitPrice"] <= 0).sum()),
        "missing_customer_id_rows": int(df_raw["CustomerID"].isnull().sum()),
        "duplicate_rows": int(df_raw.duplicated().sum()),
    }

    df = df_raw.copy()

    # Ensure InvoiceDate is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # 1. Cancelled invoices
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

    # 2. Non-positive quantities
    df = df[df["Quantity"] > 0]

    # 3. Non-positive unit prices
    df = df[df["UnitPrice"] > 0]

    # 4. Missing CustomerID
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int)

    # 5. Duplicate rows
    df = df.drop_duplicates()

    # 6. TotalAmount
    df["TotalAmount"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    stats["cleaned_rows"] = len(df)
    stats["cleaned_customers"] = int(df["CustomerID"].nunique())
    stats["cleaned_products"] = int(df["StockCode"].nunique())
    stats["cleaned_invoices"] = int(df["InvoiceNo"].nunique())
    stats["total_revenue"] = float(df["TotalAmount"].sum().round(2))

    return df, stats


def run_cleaning_pipeline(raw_file: str = RAW_FILE, cleaned_file: str = CLEANED_FILE) -> pd.DataFrame:
    """Execute the end-to-end data cleaning pipeline and save results."""
    acquire_raw_dataset(raw_file)

    print(f"Loading raw dataset from {raw_file}...")
    df_raw = pd.read_excel(raw_file, engine="openpyxl")
    print(f"Raw dataset shape: {df_raw.shape}")

    df_cleaned, stats = clean_dataset(df_raw)

    os.makedirs(os.path.dirname(cleaned_file), exist_ok=True)
    df_cleaned.to_csv(cleaned_file, index=False)
    print(f"\nCleaned dataset saved to: {cleaned_file}")
    print(f"Final record count: {len(df_cleaned):,}")
    print(f"Total Revenue: £{stats['total_revenue']:,.2f}")
    print("Data cleaning pipeline complete.")
    return df_cleaned


if __name__ == "__main__":
    # If cleaned file already exists and raw is not present, report and offer options
    if not os.path.exists(RAW_FILE) and os.path.exists(CLEANED_FILE):
        print(f"Notice: Cleaned file already exists at {CLEANED_FILE}.")
        print("To clean from source, downloading raw dataset...")
    run_cleaning_pipeline()

