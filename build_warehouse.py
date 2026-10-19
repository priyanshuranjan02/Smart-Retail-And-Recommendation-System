"""
Smart Retail Analytics — Data Warehouse ETL Pipeline
Populates the star schema from the cleaned Online Retail dataset.
Database: SQLite (retail_warehouse.db)
"""

import os
import shutil
import sqlite3
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
DB_FILE      = "data/processed/retail_warehouse.db"
SCHEMA_FILE  = "warehouse_schema.sql"

# Map countries to continental regions
REGION_MAP = {
    "United Kingdom": "Europe", "France": "Europe", "Germany": "Europe",
    "Spain": "Europe", "Netherlands": "Europe", "Belgium": "Europe",
    "Switzerland": "Europe", "Portugal": "Europe", "Italy": "Europe",
    "Finland": "Europe", "Austria": "Europe", "Norway": "Europe",
    "Sweden": "Europe", "Denmark": "Europe", "Ireland": "Europe",  # EIRE
    "EIRE": "Europe", "Channel Islands": "Europe", "Iceland": "Europe",
    "Malta": "Europe", "Cyprus": "Europe", "Greece": "Europe",
    "Poland": "Europe", "Czech Republic": "Europe", "Lithuania": "Europe",
    "European Community": "Europe",
    "USA": "North America", "Canada": "North America",
    "Brazil": "South America",
    "Australia": "Oceania",
    "Japan": "Asia", "Singapore": "Asia", "Hong Kong": "Asia",
    "United Arab Emirates": "Middle East", "Israel": "Middle East",
    "Lebanon": "Middle East", "Bahrain": "Middle East", "Saudi Arabia": "Middle East",
    "Nigeria": "Africa", "South Africa": "Africa", "RSA": "Africa",
    "Unspecified": "Unknown",
}


def build_dim_time(df: pd.DataFrame) -> pd.DataFrame:
    """Generate Dim_Time records from unique calendar dates."""
    dates = pd.to_datetime(df["InvoiceDate"]).dt.date.unique()
    time_records = []
    for d in dates:
        d_ts = pd.Timestamp(d)
        time_records.append({
            "TimeKey":      int(d_ts.strftime("%Y%m%d")),
            "FullDate":     d_ts.strftime("%Y-%m-%d"),
            "Year":         int(d_ts.year),
            "Quarter":      int(d_ts.quarter),
            "Month":        int(d_ts.month),
            "MonthName":    str(d_ts.strftime("%B")),
            "Week":         int(d_ts.isocalendar()[1]),
            "DayOfMonth":   int(d_ts.day),
            "DayOfWeek":    int(d_ts.dayofweek),
            "DayName":      str(d_ts.strftime("%A")),
            "IsWeekend":    1 if d_ts.dayofweek >= 5 else 0
        })
    return pd.DataFrame(time_records).drop_duplicates(subset="TimeKey")


def build_dim_region(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Generate Dim_Region records and lookup mapping."""
    countries = df["Country"].dropna().unique()
    region_records = []
    for i, c in enumerate(countries, start=1):
        region_records.append({
            "RegionKey": i,
            "Country":   str(c),
            "Region":    REGION_MAP.get(str(c), "Other")
        })
    dim_region = pd.DataFrame(region_records)
    lookup = dict(zip(dim_region["Country"], dim_region["RegionKey"]))
    return dim_region, lookup


def build_dim_product(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Generate Dim_Product records and lookup mapping."""
    product_agg = df.groupby("StockCode").agg(
        Description  = ("Description", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"),
        AvgUnitPrice = ("UnitPrice", "mean"),
        TimesOrdered = ("Quantity", "count")
    ).reset_index()

    product_agg.insert(0, "ProductKey", range(1, len(product_agg) + 1))
    product_agg["AvgUnitPrice"] = product_agg["AvgUnitPrice"].round(2)
    lookup = dict(zip(product_agg["StockCode"], product_agg["ProductKey"]))
    return product_agg, lookup


def build_dim_customer(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Generate Dim_Customer records and lookup mapping."""
    df_inv = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_inv["InvoiceDate"]):
        df_inv["InvoiceDate"] = pd.to_datetime(df_inv["InvoiceDate"])

    customer_agg = df_inv.groupby("CustomerID").agg(
        FirstPurchase = ("InvoiceDate", "min"),
        LastPurchase  = ("InvoiceDate", "max"),
        TotalOrders   = ("InvoiceNo", "nunique"),
        TotalSpend    = ("TotalAmount", "sum"),
        Country       = ("Country", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown")
    ).reset_index()

    customer_agg.insert(0, "CustomerKey", range(1, len(customer_agg) + 1))
    customer_agg["FirstPurchase"] = customer_agg["FirstPurchase"].dt.strftime("%Y-%m-%d")
    customer_agg["LastPurchase"]  = customer_agg["LastPurchase"].dt.strftime("%Y-%m-%d")
    customer_agg["TotalSpend"]    = customer_agg["TotalSpend"].round(2)
    customer_agg["CustomerID"]    = customer_agg["CustomerID"].astype(int)

    lookup = dict(zip(customer_agg["CustomerID"], customer_agg["CustomerKey"]))
    return customer_agg, lookup


def build_fact_sales(
    df: pd.DataFrame,
    customer_lookup: dict,
    product_lookup: dict,
    region_lookup: dict
) -> pd.DataFrame:
    """Construct Fact_Sales table linking natural records to surrogate dimension keys."""
    df_fact = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_fact["InvoiceDate"]):
        df_fact["InvoiceDate"] = pd.to_datetime(df_fact["InvoiceDate"])

    fact = pd.DataFrame()
    fact["InvoiceNo"]   = df_fact["InvoiceNo"].astype(str)
    fact["TimeKey"]     = df_fact["InvoiceDate"].dt.strftime("%Y%m%d").astype(int)
    fact["CustomerKey"] = df_fact["CustomerID"].astype(int).map(customer_lookup)
    fact["ProductKey"]  = df_fact["StockCode"].map(product_lookup)
    fact["RegionKey"]   = df_fact["Country"].map(region_lookup)
    fact["Quantity"]    = df_fact["Quantity"].astype(int)
    fact["UnitPrice"]   = df_fact["UnitPrice"].astype(float)
    fact["TotalAmount"] = df_fact["TotalAmount"].astype(float)
    fact["InvoiceTime"] = df_fact["InvoiceDate"].dt.strftime("%H:%M:%S")

    before = len(fact)
    fact = fact.dropna(subset=["CustomerKey", "ProductKey", "RegionKey"])
    fact["CustomerKey"] = fact["CustomerKey"].astype(int)
    fact["ProductKey"] = fact["ProductKey"].astype(int)
    fact["RegionKey"] = fact["RegionKey"].astype(int)
    after = len(fact)
    if before != after:
        print(f"  Warning: dropped {before - after} rows with unmapped keys.")

    return fact


def build_warehouse(
    cleaned_file: str = CLEANED_FILE,
    db_file: str = DB_FILE,
    schema_file: str = SCHEMA_FILE,
    force: bool = False,
    backup: bool = True
) -> dict:
    """Builds or rebuilds the star schema SQLite warehouse safely."""
    if not os.path.exists(cleaned_file):
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_file}. Run data_cleaning.py first.")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Warehouse schema SQL not found at {schema_file}.")

    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    # Handle safe existing DB handling
    if os.path.exists(db_file):
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{db_file}.{timestamp}.bak"
            shutil.copy2(db_file, backup_path)
            print(f"Created safety backup of existing warehouse at: {backup_path}")
        os.remove(db_file)

    print("Loading cleaned dataset...")
    df = pd.read_csv(cleaned_file, parse_dates=["InvoiceDate"])
    print(f"  Records loaded: {len(df):,}")

    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    print("Creating warehouse schema...")
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    print("  Schema created successfully.")

    # Populate dimensions
    print("Populating Dim_Time...")
    dim_time = build_dim_time(df)
    dim_time.to_sql("Dim_Time", conn, if_exists="append", index=False)
    print(f"  Dim_Time rows: {len(dim_time)}")

    print("Populating Dim_Region...")
    dim_region, region_lookup = build_dim_region(df)
    dim_region.to_sql("Dim_Region", conn, if_exists="append", index=False)
    print(f"  Dim_Region rows: {len(dim_region)}")

    print("Populating Dim_Product...")
    dim_product, product_lookup = build_dim_product(df)
    dim_product.to_sql("Dim_Product", conn, if_exists="append", index=False)
    print(f"  Dim_Product rows: {len(dim_product)}")

    print("Populating Dim_Customer...")
    dim_customer, customer_lookup = build_dim_customer(df)
    dim_customer.to_sql("Dim_Customer", conn, if_exists="append", index=False)
    print(f"  Dim_Customer rows: {len(dim_customer)}")

    print("Populating Fact_Sales (this may take a moment)...")
    fact_sales = build_fact_sales(df, customer_lookup, product_lookup, region_lookup)
    fact_sales.to_sql("Fact_Sales", conn, if_exists="append", index=False)
    print(f"  Fact_Sales rows: {len(fact_sales):,}")

    # Validation
    stats = {}
    for table in ["Dim_Time", "Dim_Customer", "Dim_Product", "Dim_Region", "Fact_Sales"]:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        stats[table] = count

    rev_res = cursor.execute("SELECT ROUND(SUM(TotalAmount), 2) FROM Fact_Sales").fetchone()[0]
    stats["TotalRevenue"] = float(rev_res)

    print("\n" + "=" * 60)
    print("WAREHOUSE VALIDATION SUMMARY")
    print("=" * 60)
    for table, count in stats.items():
        if table != "TotalRevenue":
            print(f"  {table:20s} {count:>10,}")
    print(f"\n  Total Revenue: £{stats['TotalRevenue']:,.2f}")

    conn.close()
    print(f"\nWarehouse saved to: {db_file}")
    print("ETL pipeline complete.")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Build Smart Retail Data Warehouse")
    parser.add_argument("--cleaned-file", default=CLEANED_FILE, help="Path to cleaned CSV")
    parser.add_argument("--db-file", default=DB_FILE, help="Path to target SQLite DB")
    parser.add_argument("--schema-file", default=SCHEMA_FILE, help="Path to SQL schema")
    parser.add_argument("--force", action="store_true", help="Force rebuild without backup")
    parser.add_argument("--no-backup", action="store_true", help="Do not create backup of existing DB")

    args = parser.parse_args()
    build_warehouse(
        cleaned_file=args.cleaned_file,
        db_file=args.db_file,
        schema_file=args.schema_file,
        force=args.force,
        backup=not args.no_backup
    )


if __name__ == "__main__":
    main()
