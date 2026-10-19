"""
Smart Retail Analytics — Business Intelligence Queries & OLAP Operations
Executes analytical SQL queries against the retail data warehouse.
Provides reusable, parameterized functions for dashboard integration.
"""

import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, List

DB_FILE = "data/processed/retail_warehouse.db"


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys and row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_query(title: str, sql: str, conn: Optional[sqlite3.Connection] = None, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute an analytical query and print the results as a formatted table."""
    close_at_end = False
    if conn is None:
        conn = get_connection()
        close_at_end = True

    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print(f"\nSQL:\n{sql.strip()}\n")
    df = pd.read_sql_query(sql, conn, params=params or ())
    print(df.to_string(index=False))
    print(f"\n({len(df)} rows)")

    if close_at_end:
        conn.close()
    return df


# ──────────────────────────────────────────────
# PARAMETERIZED QUERY UTILITIES FOR DASHBOARD
# ──────────────────────────────────────────────

def get_kpis(conn: sqlite3.Connection, country: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Calculate executive overview KPIs with optional filtering."""
    where_clauses = []
    params = []

    if country and country != "All":
        where_clauses.append("r.Country = ?")
        params.append(country)
    if start_date:
        where_clauses.append("t.FullDate >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("t.FullDate <= ?")
        params.append(end_date)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = f"""
        SELECT
            COUNT(DISTINCT f.InvoiceNo)           AS TotalOrders,
            COUNT(DISTINCT f.CustomerKey)         AS UniqueCustomers,
            COUNT(DISTINCT f.ProductKey)          AS UniqueProducts,
            COALESCE(SUM(f.Quantity), 0)          AS TotalUnitsSold,
            COALESCE(ROUND(SUM(f.TotalAmount), 2), 0.0) AS GrossRevenue,
            COALESCE(ROUND(AVG(f.TotalAmount), 2), 0.0) AS AvgLineItemValue,
            CASE 
                WHEN COUNT(DISTINCT f.InvoiceNo) > 0 
                THEN ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2)
                ELSE 0.0 
            END                                   AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        JOIN Dim_Region r ON f.RegionKey = r.RegionKey
        {where_sql}
    """
    row = conn.execute(sql, params).fetchone()
    return {
        "TotalOrders": int(row[0]),
        "UniqueCustomers": int(row[1]),
        "UniqueProducts": int(row[2]),
        "TotalUnitsSold": int(row[3]),
        "GrossRevenue": float(row[4]),
        "AvgLineItemValue": float(row[5]),
        "AvgOrderValue": float(row[6]),
    }


def get_monthly_sales(conn: sqlite3.Connection, country: Optional[str] = None) -> pd.DataFrame:
    """Retrieve monthly sales trends with optional country filter."""
    where_sql = "WHERE r.Country = ?" if country and country != "All" else ""
    params = (country,) if country and country != "All" else ()

    sql = f"""
        SELECT
            t.Year,
            t.Month,
            t.MonthName,
            t.Year || '-' || PRINTF('%02d', t.Month) AS YearMonth,
            COUNT(DISTINCT f.InvoiceNo)         AS TotalOrders,
            SUM(f.Quantity)                     AS TotalUnitsSold,
            ROUND(SUM(f.TotalAmount), 2)        AS TotalRevenue,
            ROUND(AVG(f.TotalAmount), 2)        AS AvgOrderLineValue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        JOIN Dim_Region r ON f.RegionKey = r.RegionKey
        {where_sql}
        GROUP BY t.Year, t.Month, t.MonthName
        ORDER BY t.Year, t.Month
    """
    return pd.read_sql_query(sql, conn, params=params)


def get_monthly_growth(conn: sqlite3.Connection) -> pd.DataFrame:
    """Retrieve Month-over-Month Revenue Growth with safe division."""
    sql = """
        WITH monthly AS (
            SELECT
                t.Year * 100 + t.Month          AS YearMonthKey,
                t.Year,
                t.Month,
                t.MonthName,
                t.Year || '-' || PRINTF('%02d', t.Month) AS YearMonth,
                ROUND(SUM(f.TotalAmount), 2)    AS Revenue,
                COUNT(DISTINCT f.InvoiceNo)     AS Orders,
                SUM(f.Quantity)                 AS UnitsSold
            FROM Fact_Sales f
            JOIN Dim_Time t ON f.TimeKey = t.TimeKey
            GROUP BY t.Year, t.Month, t.MonthName
        )
        SELECT
            m.Year,
            m.Month,
            m.MonthName,
            m.YearMonth,
            m.Revenue,
            m.Orders,
            m.UnitsSold,
            LAG(m.Revenue) OVER (ORDER BY m.YearMonthKey) AS PrevMonthRevenue,
            CASE 
                WHEN LAG(m.Revenue) OVER (ORDER BY m.YearMonthKey) IS NULL OR LAG(m.Revenue) OVER (ORDER BY m.YearMonthKey) = 0 THEN 0.0
                ELSE ROUND(
                    (m.Revenue - LAG(m.Revenue) OVER (ORDER BY m.YearMonthKey)) * 100.0 / LAG(m.Revenue) OVER (ORDER BY m.YearMonthKey), 
                    2
                )
            END AS GrowthPct
        FROM monthly m
        ORDER BY m.YearMonthKey
    """
    return pd.read_sql_query(sql, conn)


def get_country_sales(conn: sqlite3.Connection, limit: Optional[int] = None) -> pd.DataFrame:
    """Retrieve sales by country and region with revenue share %."""
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    sql = f"""
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
        {limit_clause}
    """
    return pd.read_sql_query(sql, conn)


def get_top_products(conn: sqlite3.Connection, limit: int = 10, order_by: str = "revenue", country: Optional[str] = None) -> pd.DataFrame:
    """Retrieve top products ranked by revenue, quantity, or order frequency."""
    order_col = {
        "revenue": "TotalRevenue",
        "units": "TotalUnitsSold",
        "orders": "TimesOrdered"
    }.get(order_by.lower(), "TotalRevenue")

    where_sql = "WHERE r.Country = ?" if country and country != "All" else ""
    params = (country,) if country and country != "All" else ()

    sql = f"""
        SELECT
            p.StockCode,
            COALESCE(p.Description, 'Unknown Product') AS Description,
            SUM(f.Quantity)                     AS TotalUnitsSold,
            COUNT(DISTINCT f.InvoiceNo)         AS TimesOrdered,
            ROUND(AVG(f.UnitPrice), 2)          AS AvgPrice,
            ROUND(SUM(f.TotalAmount), 2)        AS TotalRevenue,
            ROUND(SUM(f.TotalAmount) * 100.0 / 
                  (SELECT SUM(TotalAmount) FROM Fact_Sales), 2) AS RevenueContributionPct
        FROM Fact_Sales f
        JOIN Dim_Product p ON f.ProductKey = p.ProductKey
        JOIN Dim_Region r ON f.RegionKey = r.RegionKey
        {where_sql}
        GROUP BY p.StockCode, p.Description
        ORDER BY {order_col} DESC
        LIMIT {int(limit)}
    """
    return pd.read_sql_query(sql, conn, params=params)


def get_top_customers(conn: sqlite3.Connection, limit: int = 20) -> pd.DataFrame:
    """Retrieve top customers by lifetime spend."""
    sql = f"""
        SELECT
            c.CustomerID,
            c.Country,
            c.FirstPurchase,
            c.LastPurchase,
            COUNT(DISTINCT f.InvoiceNo)         AS TotalOrders,
            SUM(f.Quantity)                     AS TotalUnitsBought,
            ROUND(SUM(f.TotalAmount), 2)        AS LifetimeSpend,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey
        GROUP BY c.CustomerID, c.Country, c.FirstPurchase, c.LastPurchase
        ORDER BY LifetimeSpend DESC
        LIMIT {int(limit)}
    """
    return pd.read_sql_query(sql, conn)


def get_retention_breakdown(conn: sqlite3.Connection) -> pd.DataFrame:
    """Segment customers by order count: One-Time, Returning (2-5), Loyal (6+)."""
    sql = """
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
    """
    return pd.read_sql_query(sql, conn)


def get_sales_by_day_of_week(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calculate revenue and order count aggregated by day of week."""
    sql = """
        SELECT
            t.DayOfWeek,
            t.DayName,
            COUNT(DISTINCT f.InvoiceNo)         AS Orders,
            SUM(f.Quantity)                     AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2)        AS Revenue,
            ROUND(SUM(f.TotalAmount) / COUNT(DISTINCT f.InvoiceNo), 2) AS AvgOrderValue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.DayOfWeek, t.DayName
        ORDER BY t.DayOfWeek
    """
    return pd.read_sql_query(sql, conn)


def get_sales_by_region(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calculate revenue and market share by continental region."""
    sql = """
        SELECT
            r.Region,
            COUNT(DISTINCT r.Country)           AS Countries,
            COUNT(DISTINCT f.CustomerKey)       AS Customers,
            SUM(f.Quantity)                     AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2)        AS Revenue,
            ROUND(SUM(f.TotalAmount) * 100.0 /
                  (SELECT SUM(TotalAmount) FROM Fact_Sales), 2)
                                                AS SharePct
        FROM Fact_Sales f
        JOIN Dim_Region r ON f.RegionKey = r.RegionKey
        GROUP BY r.Region
        ORDER BY Revenue DESC
    """
    return pd.read_sql_query(sql, conn)


def execute_safe_query(conn: sqlite3.Connection, sql: str, max_rows: int = 200) -> pd.DataFrame:
    """
    Executes a read-only SQL query safely.
    Rejects any destructive or schema-altering commands (DROP, DELETE, INSERT, UPDATE, ALTER, ATTACH).
    """
    cleaned_sql = sql.strip()
    first_word = cleaned_sql.split()[0].upper() if cleaned_sql else ""
    if first_word not in ("SELECT", "WITH", "EXPLAIN"):
        raise ValueError("Only read-only SELECT or WITH queries are permitted in the warehouse explorer.")

    disallowed_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "REPLACE", "CREATE", "ATTACH", "DETACH"]
    upper_sql = cleaned_sql.upper()
    for kw in disallowed_keywords:
        # Check as isolated token
        tokens = upper_sql.split()
        if kw in tokens:
            raise ValueError(f"Disallowed DDL/DML keyword '{kw}' detected. Only SELECT statements are permitted.")

    # Wrap in limit if not present
    if "LIMIT" not in upper_sql:
        cleaned_sql += f" LIMIT {max_rows}"

    return pd.read_sql_query(cleaned_sql, conn)


def main():
    """Execute all 15+ standard BI queries against the warehouse and print formatted reports."""
    conn = get_connection()

    # 1. Total Sales by Month
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
    """, conn)

    # 2. Sales by Country
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
    """, conn)

    # 3. Top 10 Products by Revenue
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
    """, conn)

    # 4. Top 20 Customers
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
    """, conn)

    # Drill-down queries
    run_query("DRILL-DOWN Level 1: Revenue by YEAR", """
        SELECT
            t.Year,
            ROUND(SUM(f.TotalAmount), 2)        AS Revenue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year
        ORDER BY t.Year
    """, conn)

    run_query("DRILL-DOWN Level 2: Revenue by YEAR → QUARTER", """
        SELECT
            t.Year,
            t.Quarter,
            ROUND(SUM(f.TotalAmount), 2)        AS Revenue
        FROM Fact_Sales f
        JOIN Dim_Time t ON f.TimeKey = t.TimeKey
        GROUP BY t.Year, t.Quarter
        ORDER BY t.Year, t.Quarter
    """, conn)

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
    """, conn)

    # Roll-up queries
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
    """, conn)

    # Slice & Dice
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
    """, conn)

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
    """, conn)

    # Dashboard KPIs
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
    """, conn)

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
    """, conn)

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
    """, conn)

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
    """, conn)

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
    """, conn)

    conn.close()
    print("\n\nAll BI queries executed successfully.")


if __name__ == "__main__":
    main()
