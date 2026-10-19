"""
Smart Retail Analytics — Data Warehouse ETL Pipeline
Populates the star schema from the cleaned Online Retail dataset.
Database: SQLite (retail_warehouse.db)
"""

import os
import sqlite3
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

CLEANED_FILE = "data/cleaned/online_retail_cleaned.csv"
DB_FILE      = "data/processed/retail_warehouse.db"
SCHEMA_FILE  = "warehouse_schema.sql"

os.makedirs("data/processed", exist_ok=True)

# ──────────────────────────────────────────────
# 1. LOAD CLEANED DATASET
# ──────────────────────────────────────────────

print("Loading cleaned dataset...")
df = pd.read_csv(CLEANED_FILE, parse_dates=["InvoiceDate"])
print(f"  Records loaded: {len(df):,}")

# ──────────────────────────────────────────────
# 2. CREATE DATABASE & EXECUTE SCHEMA DDL
# ──────────────────────────────────────────────

# Remove existing DB to start fresh
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

print("Creating warehouse schema...")
with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
    schema_sql = f.read()
cursor.executescript(schema_sql)
conn.commit()
print("  Schema created successfully.")

# ──────────────────────────────────────────────
# 3. POPULATE Dim_Time
# ──────────────────────────────────────────────
# One row per unique calendar date in the dataset.

print("Populating Dim_Time...")

dates = df["InvoiceDate"].dt.date.unique()
time_records = []

for d in dates:
    d_ts = pd.Timestamp(d)
    time_records.append({
        "TimeKey":      int(d_ts.strftime("%Y%m%d")),    # e.g. 20110101
        "FullDate":     d_ts.strftime("%Y-%m-%d"),
        "Year":         d_ts.year,
        "Quarter":      d_ts.quarter,
        "Month":        d_ts.month,
        "MonthName":    d_ts.strftime("%B"),              # 'January', ...
        "Week":         d_ts.isocalendar()[1],
        "DayOfMonth":   d_ts.day,
        "DayOfWeek":    d_ts.dayofweek,                   # 0=Mon
        "DayName":      d_ts.strftime("%A"),              # 'Monday', ...
        "IsWeekend":    1 if d_ts.dayofweek >= 5 else 0
    })

dim_time = pd.DataFrame(time_records).drop_duplicates(subset="TimeKey")
dim_time.to_sql("Dim_Time", conn, if_exists="append", index=False)
print(f"  Dim_Time rows: {len(dim_time)}")

# ──────────────────────────────────────────────
# 4. POPULATE Dim_Region
# ──────────────────────────────────────────────
# One row per unique Country. Region is a broader grouping.

print("Populating Dim_Region...")

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

countries = df["Country"].unique()
region_records = []
for i, c in enumerate(countries, start=1):
    region_records.append({
        "RegionKey": i,
        "Country":   c,
        "Region":    REGION_MAP.get(c, "Other")
    })

dim_region = pd.DataFrame(region_records)
dim_region.to_sql("Dim_Region", conn, if_exists="append", index=False)
print(f"  Dim_Region rows: {len(dim_region)}")

# Build lookup: Country -> RegionKey
region_lookup = dict(zip(dim_region["Country"], dim_region["RegionKey"]))

# ──────────────────────────────────────────────
# 5. POPULATE Dim_Product
# ──────────────────────────────────────────────
# One row per unique StockCode.

print("Populating Dim_Product...")

product_agg = df.groupby("StockCode").agg(
    Description  = ("Description", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"),
    AvgUnitPrice = ("UnitPrice", "mean"),
    TimesOrdered = ("Quantity", "count")
).reset_index()

product_agg.insert(0, "ProductKey", range(1, len(product_agg) + 1))
product_agg["AvgUnitPrice"] = product_agg["AvgUnitPrice"].round(2)

product_agg.to_sql("Dim_Product", conn, if_exists="append", index=False)
print(f"  Dim_Product rows: {len(product_agg)}")

# Build lookup: StockCode -> ProductKey
product_lookup = dict(zip(product_agg["StockCode"], product_agg["ProductKey"]))

# ──────────────────────────────────────────────
# 6. POPULATE Dim_Customer
# ──────────────────────────────────────────────
# One row per unique CustomerID.

print("Populating Dim_Customer...")

customer_agg = df.groupby("CustomerID").agg(
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

customer_agg.to_sql("Dim_Customer", conn, if_exists="append", index=False)
print(f"  Dim_Customer rows: {len(customer_agg)}")

# Build lookup: CustomerID -> CustomerKey
customer_lookup = dict(zip(customer_agg["CustomerID"], customer_agg["CustomerKey"]))

# ──────────────────────────────────────────────
# 7. POPULATE Fact_Sales
# ──────────────────────────────────────────────
# One row per invoice line item (same grain as cleaned dataset).

print("Populating Fact_Sales (this may take a moment)...")

fact = df[["InvoiceNo", "InvoiceDate", "CustomerID", "StockCode",
           "Country", "Quantity", "UnitPrice", "TotalAmount"]].copy()

# Map natural keys to surrogate keys
fact["TimeKey"]     = fact["InvoiceDate"].dt.strftime("%Y%m%d").astype(int)
fact["CustomerKey"] = fact["CustomerID"].map(customer_lookup)
fact["ProductKey"]  = fact["StockCode"].map(product_lookup)
fact["RegionKey"]   = fact["Country"].map(region_lookup)
fact["InvoiceTime"] = fact["InvoiceDate"].dt.strftime("%H:%M:%S")
fact["InvoiceNo"]   = fact["InvoiceNo"].astype(str)

# Select final columns (SalesKey is auto-generated)
fact_final = fact[["InvoiceNo", "TimeKey", "CustomerKey", "ProductKey",
                   "RegionKey", "Quantity", "UnitPrice", "TotalAmount",
                   "InvoiceTime"]]

# Drop any rows with unmapped keys
before = len(fact_final)
fact_final = fact_final.dropna(subset=["CustomerKey", "ProductKey", "RegionKey"])
after = len(fact_final)
if before != after:
    print(f"  Warning: dropped {before - after} rows with unmapped keys.")

fact_final.to_sql("Fact_Sales", conn, if_exists="append", index=False)
print(f"  Fact_Sales rows: {len(fact_final):,}")

# ──────────────────────────────────────────────
# 8. VALIDATION — Run sample OLAP queries
# ──────────────────────────────────────────────

print("\n" + "=" * 60)
print("WAREHOUSE VALIDATION QUERIES")
print("=" * 60)

# Row counts
print("\n--- Table Row Counts ---")
for table in ["Dim_Time", "Dim_Customer", "Dim_Product", "Dim_Region", "Fact_Sales"]:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:20s} {count:>10,}")

# Total revenue
print("\n--- Total Revenue ---")
result = cursor.execute("SELECT ROUND(SUM(TotalAmount), 2) FROM Fact_Sales").fetchone()
print(f"  Total: £{result[0]:,.2f}")

# Revenue by year
print("\n--- Revenue by Year ---")
rows = cursor.execute("""
    SELECT t.Year, ROUND(SUM(f.TotalAmount), 2) AS Revenue, COUNT(*) AS Transactions
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year
    ORDER BY t.Year
""").fetchall()
for r in rows:
    print(f"  {r[0]}  Revenue: £{r[1]:>12,.2f}  Transactions: {r[2]:>10,}")

# Top 5 countries by revenue
print("\n--- Top 5 Countries by Revenue ---")
rows = cursor.execute("""
    SELECT r.Country, ROUND(SUM(f.TotalAmount), 2) AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Region r ON f.RegionKey = r.RegionKey
    GROUP BY r.Country
    ORDER BY Revenue DESC
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]:25s} £{r[1]:>12,.2f}")

# Top 5 products by quantity sold
print("\n--- Top 5 Products by Quantity Sold ---")
rows = cursor.execute("""
    SELECT p.Description, SUM(f.Quantity) AS TotalQty
    FROM Fact_Sales f
    JOIN Dim_Product p ON f.ProductKey = p.ProductKey
    GROUP BY p.StockCode
    ORDER BY TotalQty DESC
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0][:40]:40s} {r[1]:>10,}")

# Monthly trend
print("\n--- Monthly Revenue Trend (sample) ---")
rows = cursor.execute("""
    SELECT t.Year, t.Month, t.MonthName, ROUND(SUM(f.TotalAmount), 2) AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year, t.Month
    ORDER BY t.Year, t.Month
    LIMIT 6
""").fetchall()
for r in rows:
    print(f"  {r[0]}-{r[2]:10s} £{r[3]:>12,.2f}")

conn.close()
print(f"\nWarehouse saved to: {DB_FILE}")
print("ETL pipeline complete.")
