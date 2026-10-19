"""
Smart Retail Analytics — Business Intelligence Queries
Runs analytical SQL queries against the retail data warehouse.
"""

import sqlite3
import pandas as pd

DB_FILE = "data/processed/retail_warehouse.db"
conn = sqlite3.connect(DB_FILE)

def run_query(title, sql):
    """Execute a query and print the results as a formatted table."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print(f"\nSQL:\n{sql.strip()}\n")
    df = pd.read_sql_query(sql, conn)
    print(df.to_string(index=False))
    print(f"\n({len(df)} rows)")
    return df


# ══════════════════════════════════════════════════════════════════════
# QUERY 1: TOTAL SALES BY MONTH
# ══════════════════════════════════════════════════════════════════════

run_query("Q1: TOTAL SALES BY MONTH", """
    SELECT
        t.Year,
        t.Month,
        t.MonthName,
        COUNT(DISTINCT f.InvoiceNo)         AS TotalOrders,
        SUM(f.Quantity)                     AS TotalUnitsSold,
        ROUND(SUM(f.TotalAmount), 2)        AS TotalRevenue,
        ROUND(AVG(f.TotalAmount), 2)        AS AvgOrderLineValue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year, t.Month
    ORDER BY t.Year, t.Month
""")


# ══════════════════════════════════════════════════════════════════════
# QUERY 2: SALES BY COUNTRY
# ══════════════════════════════════════════════════════════════════════

run_query("Q2: SALES BY COUNTRY (Top 15)", """
    SELECT
        r.Country,
        r.Region,
        COUNT(DISTINCT f.InvoiceNo)         AS TotalOrders,
        COUNT(DISTINCT f.CustomerKey)       AS UniqueCustomers,
        SUM(f.Quantity)                     AS TotalUnitsSold,
        ROUND(SUM(f.TotalAmount), 2)        AS TotalRevenue,
        ROUND(SUM(f.TotalAmount) * 100.0 /
              (SELECT SUM(TotalAmount) FROM Fact_Sales), 2)
                                            AS RevenueSharePct
    FROM Fact_Sales f
    JOIN Dim_Region r ON f.RegionKey = r.RegionKey
    GROUP BY r.Country, r.Region
    ORDER BY TotalRevenue DESC
    LIMIT 15
""")


# ══════════════════════════════════════════════════════════════════════
# QUERY 3: TOP 10 PRODUCTS BY REVENUE
# ══════════════════════════════════════════════════════════════════════

run_query("Q3: TOP 10 PRODUCTS BY REVENUE", """
    SELECT
        p.StockCode,
        p.Description,
        SUM(f.Quantity)                     AS TotalUnitsSold,
        COUNT(DISTINCT f.InvoiceNo)         AS TimesOrdered,
        ROUND(AVG(f.UnitPrice), 2)          AS AvgPrice,
        ROUND(SUM(f.TotalAmount), 2)        AS TotalRevenue
    FROM Fact_Sales f
    JOIN Dim_Product p ON f.ProductKey = p.ProductKey
    GROUP BY p.StockCode, p.Description
    ORDER BY TotalRevenue DESC
    LIMIT 10
""")


# ══════════════════════════════════════════════════════════════════════
# QUERY 4: CUSTOMER-WISE SALES (Top 20 Customers)
# ══════════════════════════════════════════════════════════════════════

run_query("Q4: TOP 20 CUSTOMERS BY LIFETIME SPEND", """
    SELECT
        c.CustomerID,
        c.Country,
        c.FirstPurchase,
        c.LastPurchase,
        COUNT(DISTINCT f.InvoiceNo)         AS TotalOrders,
        SUM(f.Quantity)                     AS TotalUnitsBought,
        ROUND(SUM(f.TotalAmount), 2)        AS LifetimeSpend,
        ROUND(SUM(f.TotalAmount) /
              COUNT(DISTINCT f.InvoiceNo), 2)
                                            AS AvgOrderValue
    FROM Fact_Sales f
    JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey
    GROUP BY c.CustomerID
    ORDER BY LifetimeSpend DESC
    LIMIT 20
""")


# ══════════════════════════════════════════════════════════════════════
# OLAP OPERATIONS: ROLL-UP AND DRILL-DOWN
# ══════════════════════════════════════════════════════════════════════

print("\n\n" + "#" * 70)
print("  OLAP OPERATIONS: ROLL-UP & DRILL-DOWN")
print("#" * 70)

# ── DRILL-DOWN: Year → Quarter → Month ──
# Start at the highest level (Year), then break into finer granularity.

run_query("DRILL-DOWN Level 1: Revenue by YEAR", """
    SELECT
        t.Year,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year
    ORDER BY t.Year
""")

run_query("DRILL-DOWN Level 2: Revenue by YEAR → QUARTER", """
    SELECT
        t.Year,
        t.Quarter,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year, t.Quarter
    ORDER BY t.Year, t.Quarter
""")

run_query("DRILL-DOWN Level 3: Revenue by YEAR → QUARTER → MONTH", """
    SELECT
        t.Year,
        t.Quarter,
        t.Month,
        t.MonthName,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.Year, t.Quarter, t.Month
    ORDER BY t.Year, t.Month
""")


# ── ROLL-UP: Day → Month → Quarter → Year ──
# Start at the most granular level and aggregate upward.

run_query("ROLL-UP: Daily → Monthly (showing Dec 2011)", """
    SELECT
        t.FullDate,
        t.DayName,
        ROUND(SUM(f.TotalAmount), 2)        AS DailyRevenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    WHERE t.Year = 2011 AND t.Month = 12
    GROUP BY t.FullDate
    ORDER BY t.FullDate
""")

run_query("ROLL-UP: rolled up to Monthly (Dec 2011 total)", """
    SELECT
        t.Year,
        t.MonthName,
        ROUND(SUM(f.TotalAmount), 2)        AS MonthlyRevenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    WHERE t.Year = 2011 AND t.Month = 12
    GROUP BY t.Year, t.Month
""")


# ── SLICE: Fix one dimension, view the rest ──

run_query("SLICE: Sales for 'United Kingdom' only, by month", """
    SELECT
        t.Year,
        t.MonthName,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue,
        COUNT(DISTINCT f.InvoiceNo)         AS Orders
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    JOIN Dim_Region r ON f.RegionKey = r.RegionKey
    WHERE r.Country = 'United Kingdom'
    GROUP BY t.Year, t.Month
    ORDER BY t.Year, t.Month
""")


# ── DICE: Fix two dimensions simultaneously ──

run_query("DICE: UK sales for Q4 2011 only, by product category", """
    SELECT
        p.Description,
        SUM(f.Quantity)                     AS UnitsSold,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    JOIN Dim_Region r ON f.RegionKey = r.RegionKey
    JOIN Dim_Product p ON f.ProductKey = p.ProductKey
    WHERE r.Country = 'United Kingdom'
      AND t.Year = 2011
      AND t.Quarter = 4
    GROUP BY p.Description
    ORDER BY Revenue DESC
    LIMIT 10
""")


# ══════════════════════════════════════════════════════════════════════
# BONUS KPI QUERIES (for dashboard use)
# ══════════════════════════════════════════════════════════════════════

print("\n\n" + "#" * 70)
print("  DASHBOARD KPI QUERIES")
print("#" * 70)

run_query("KPI: Overall Summary Metrics", """
    SELECT
        COUNT(DISTINCT InvoiceNo)           AS TotalOrders,
        COUNT(DISTINCT CustomerKey)         AS UniqueCustomers,
        COUNT(DISTINCT ProductKey)          AS UniqueProducts,
        SUM(Quantity)                       AS TotalUnitsSold,
        ROUND(SUM(TotalAmount), 2)          AS GrossRevenue,
        ROUND(AVG(TotalAmount), 2)          AS AvgLineItemValue,
        ROUND(SUM(TotalAmount) /
              COUNT(DISTINCT InvoiceNo), 2) AS AvgOrderValue
    FROM Fact_Sales
""")

run_query("KPI: Month-over-Month Revenue Growth", """
    WITH monthly AS (
        SELECT
            t.Year * 100 + t.Month          AS YearMonth,
            t.Year,
            t.MonthName,
            ROUND(SUM(f.TotalAmount), 2)    AS Revenue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year, t.Month
    )
    SELECT
        m.Year,
        m.MonthName,
        m.Revenue,
        LAG(m.Revenue) OVER (ORDER BY m.YearMonth)
                                            AS PrevMonthRevenue,
        ROUND(
            (m.Revenue - LAG(m.Revenue) OVER (ORDER BY m.YearMonth))
            * 100.0
            / LAG(m.Revenue) OVER (ORDER BY m.YearMonth),
            2
        )                                   AS GrowthPct
    FROM monthly m
    ORDER BY m.YearMonth
""")

run_query("KPI: Customer Retention — Repeat vs One-Time Buyers", """
    SELECT
        CASE
            WHEN OrderCount = 1 THEN 'One-Time Buyer'
            WHEN OrderCount BETWEEN 2 AND 5 THEN 'Returning (2-5 orders)'
            WHEN OrderCount > 5 THEN 'Loyal (6+ orders)'
        END                                 AS CustomerType,
        COUNT(*)                            AS CustomerCount,
        ROUND(COUNT(*) * 100.0 /
              (SELECT COUNT(DISTINCT CustomerKey) FROM Fact_Sales), 2)
                                            AS Pct
    FROM (
        SELECT CustomerKey, COUNT(DISTINCT InvoiceNo) AS OrderCount
        FROM Fact_Sales
        GROUP BY CustomerKey
    )
    GROUP BY CustomerType
    ORDER BY CustomerCount DESC
""")

run_query("KPI: Revenue by Day of Week", """
    SELECT
        t.DayName,
        t.DayOfWeek,
        COUNT(DISTINCT f.InvoiceNo)         AS Orders,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue
    FROM Fact_Sales f
    JOIN Dim_Time t ON f.TimeKey = t.TimeKey
    GROUP BY t.DayOfWeek, t.DayName
    ORDER BY t.DayOfWeek
""")

run_query("KPI: Revenue by Region (Continental)", """
    SELECT
        r.Region,
        COUNT(DISTINCT r.Country)           AS Countries,
        COUNT(DISTINCT f.CustomerKey)       AS Customers,
        ROUND(SUM(f.TotalAmount), 2)        AS Revenue,
        ROUND(SUM(f.TotalAmount) * 100.0 /
              (SELECT SUM(TotalAmount) FROM Fact_Sales), 2)
                                            AS SharePct
    FROM Fact_Sales f
    JOIN Dim_Region r ON f.RegionKey = r.RegionKey
    GROUP BY r.Region
    ORDER BY Revenue DESC
""")


conn.close()
print("\n\nAll BI queries executed successfully.")
