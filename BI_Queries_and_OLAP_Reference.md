# BI Analytics — OLAP Operations & KPI Reference

**Project:** Smart Retail Analytics & Recommendation Warehouse

---

## 1. Core Analytical Queries

All queries run against the star schema in `retail_warehouse.db`. Executable script: `bi_queries.py`.

### Q1: Total Sales by Month
```sql
SELECT
    t.Year,
    t.Month,
    t.MonthName,
    COUNT(DISTINCT f.InvoiceNo)      AS TotalOrders,
    SUM(f.Quantity)                  AS TotalUnitsSold,
    ROUND(SUM(f.TotalAmount), 2)     AS TotalRevenue,
    ROUND(AVG(f.TotalAmount), 2)     AS AvgOrderLineValue
FROM Fact_Sales f
JOIN Dim_Time t ON f.TimeKey = t.TimeKey
GROUP BY t.Year, t.Month
ORDER BY t.Year, t.Month;
```
**Use case:** Identify seasonal trends, peak/trough months, and year-over-year growth.

---

### Q2: Sales by Country
```sql
SELECT
    r.Country,
    r.Region,
    COUNT(DISTINCT f.InvoiceNo)      AS TotalOrders,
    COUNT(DISTINCT f.CustomerKey)    AS UniqueCustomers,
    SUM(f.Quantity)                  AS TotalUnitsSold,
    ROUND(SUM(f.TotalAmount), 2)     AS TotalRevenue,
    ROUND(SUM(f.TotalAmount) * 100.0 /
          (SELECT SUM(TotalAmount) FROM Fact_Sales), 2)
                                     AS RevenueSharePct
FROM Fact_Sales f
JOIN Dim_Region r ON f.RegionKey = r.RegionKey
GROUP BY r.Country, r.Region
ORDER BY TotalRevenue DESC;
```
**Use case:** Geographic revenue distribution, market penetration analysis, expansion targeting.

---

### Q3: Top 10 Products by Revenue
```sql
SELECT
    p.StockCode,
    p.Description,
    SUM(f.Quantity)                  AS TotalUnitsSold,
    COUNT(DISTINCT f.InvoiceNo)      AS TimesOrdered,
    ROUND(AVG(f.UnitPrice), 2)       AS AvgPrice,
    ROUND(SUM(f.TotalAmount), 2)     AS TotalRevenue
FROM Fact_Sales f
JOIN Dim_Product p ON f.ProductKey = p.ProductKey
GROUP BY p.StockCode, p.Description
ORDER BY TotalRevenue DESC
LIMIT 10;
```
**Use case:** Identify best-sellers, high-margin products, and candidates for promotion.

---

### Q4: Customer-Wise Sales (Top 20)
```sql
SELECT
    c.CustomerID,
    c.Country,
    c.FirstPurchase,
    c.LastPurchase,
    COUNT(DISTINCT f.InvoiceNo)      AS TotalOrders,
    SUM(f.Quantity)                  AS TotalUnitsBought,
    ROUND(SUM(f.TotalAmount), 2)     AS LifetimeSpend,
    ROUND(SUM(f.TotalAmount) /
          COUNT(DISTINCT f.InvoiceNo), 2)
                                     AS AvgOrderValue
FROM Fact_Sales f
JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey
GROUP BY c.CustomerID
ORDER BY LifetimeSpend DESC
LIMIT 20;
```
**Use case:** High-value customer identification, VIP programme targeting, CLV estimation.

---

## 2. OLAP Operations Explained

OLAP (Online Analytical Processing) allows multi-dimensional exploration of data. The star schema supports four core operations:

### 2.1 Drill-Down (High → Low granularity)

Navigate from a summarised view into finer detail by adding a dimension attribute.

```
Year  →  Year + Quarter  →  Year + Quarter + Month  →  Year + Quarter + Month + Day
```

```sql
-- Level 1: Revenue by Year
SELECT t.Year, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f JOIN Dim_Time t ON f.TimeKey = t.TimeKey
GROUP BY t.Year;

-- Level 2: Drill into quarters
SELECT t.Year, t.Quarter, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f JOIN Dim_Time t ON f.TimeKey = t.TimeKey
GROUP BY t.Year, t.Quarter;

-- Level 3: Drill into months
SELECT t.Year, t.Quarter, t.MonthName, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f JOIN Dim_Time t ON f.TimeKey = t.TimeKey
GROUP BY t.Year, t.Quarter, t.Month;
```

**How it works:** Each level adds another column to `GROUP BY`, splitting the aggregate into finer buckets.

---

### 2.2 Roll-Up (Low → High granularity)

The inverse of drill-down — aggregate from detailed to summarised.

```
Day  →  Month  →  Quarter  →  Year
```

```sql
-- Start: Daily revenue for December 2011
SELECT t.FullDate, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f JOIN Dim_Time t ON f.TimeKey = t.TimeKey
WHERE t.Year = 2011 AND t.Month = 12
GROUP BY t.FullDate;

-- Roll up to: Monthly total
SELECT t.MonthName, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f JOIN Dim_Time t ON f.TimeKey = t.TimeKey
WHERE t.Year = 2011 AND t.Month = 12
GROUP BY t.Month;
```

**How it works:** Remove columns from `GROUP BY` to merge rows into broader aggregates.

---

### 2.3 Slice (Fix one dimension)

Fix one dimension to a single value and view all other dimensions.

```sql
-- Slice: Fix Country = 'United Kingdom', view monthly sales
SELECT t.Year, t.MonthName, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f
JOIN Dim_Time t ON f.TimeKey = t.TimeKey
JOIN Dim_Region r ON f.RegionKey = r.RegionKey
WHERE r.Country = 'United Kingdom'
GROUP BY t.Year, t.Month
ORDER BY t.Year, t.Month;
```

**How it works:** Add a `WHERE` clause on one dimension while grouping by others.

---

### 2.4 Dice (Fix two+ dimensions)

Fix two or more dimensions simultaneously.

```sql
-- Dice: UK + Q4 2011, view top products
SELECT p.Description, ROUND(SUM(f.TotalAmount), 2) AS Revenue
FROM Fact_Sales f
JOIN Dim_Time t ON f.TimeKey = t.TimeKey
JOIN Dim_Region r ON f.RegionKey = r.RegionKey
JOIN Dim_Product p ON f.ProductKey = p.ProductKey
WHERE r.Country = 'United Kingdom'
  AND t.Year = 2011 AND t.Quarter = 4
GROUP BY p.Description
ORDER BY Revenue DESC
LIMIT 10;
```

**How it works:** Multiple `WHERE` conditions across different dimensions.

---

## 3. Recommended KPIs for Retail Sales Dashboard

### 3.1 Revenue & Sales KPIs

| KPI | Formula | SQL Expression |
|---|---|---|
| **Gross Revenue** | Sum of all TotalAmount | `SUM(TotalAmount)` |
| **Average Order Value (AOV)** | Revenue ÷ Unique Orders | `SUM(TotalAmount) / COUNT(DISTINCT InvoiceNo)` |
| **Average Line Item Value** | Revenue ÷ Line Items | `AVG(TotalAmount)` |
| **Month-over-Month Growth** | (Current − Previous) ÷ Previous × 100 | `LAG()` window function |
| **Revenue per Customer** | Revenue ÷ Unique Customers | `SUM(TotalAmount) / COUNT(DISTINCT CustomerKey)` |

### 3.2 Customer KPIs

| KPI | Formula | SQL Expression |
|---|---|---|
| **Total Unique Customers** | Distinct customer count | `COUNT(DISTINCT CustomerKey)` |
| **Repeat Purchase Rate** | Customers with 2+ orders ÷ Total customers | Subquery with `HAVING COUNT(DISTINCT InvoiceNo) >= 2` |
| **Customer Lifetime Value** | Avg spend per customer over total relationship | `SUM(TotalAmount) / COUNT(DISTINCT CustomerKey)` |
| **One-Time vs Returning** | Segment by order count | `CASE WHEN OrderCount = 1 THEN 'One-Time' ...` |

### 3.3 Product KPIs

| KPI | Formula | SQL Expression |
|---|---|---|
| **Top Products by Revenue** | Ranked by total sales | `ORDER BY SUM(TotalAmount) DESC` |
| **Top Products by Volume** | Ranked by units sold | `ORDER BY SUM(Quantity) DESC` |
| **Product Revenue Concentration** | Top 10% products' share of total revenue | Cumulative % query |
| **Average Units per Order** | Total qty ÷ Total orders | `SUM(Quantity) / COUNT(DISTINCT InvoiceNo)` |

### 3.4 Time & Trend KPIs

| KPI | Formula | SQL Expression |
|---|---|---|
| **Best Performing Day** | Day of week with highest revenue | `GROUP BY DayName ORDER BY Revenue DESC` |
| **Peak Sales Hour** | Hour with highest transaction volume | `GROUP BY InvoiceTime` |
| **Seasonal Index** | Monthly revenue ÷ Overall monthly average | Window function |

### 3.5 Geography KPIs

| KPI | Formula | SQL Expression |
|---|---|---|
| **Revenue by Region** | Continental revenue breakdown | `GROUP BY Region` |
| **Market Share by Country** | Country revenue ÷ Total revenue × 100 | Subquery percentage |
| **Customer Density by Country** | Customers per country | `COUNT(DISTINCT CustomerKey) GROUP BY Country` |

---

## 4. Dashboard Layout Recommendation

```
┌───────────────────────────────────────────────────────────┐
│  HEADER: Filters (Date Range | Country | Product)         │
├───────────┬───────────┬───────────┬───────────────────────┤
│  KPI Card │  KPI Card │  KPI Card │  KPI Card             │
│  Revenue  │  Orders   │  Customers│  AOV                  │
├───────────┴───────────┴───────────┴───────────────────────┤
│  LINE CHART: Monthly Revenue Trend with MoM Growth        │
├──────────────────────────┬────────────────────────────────┤
│  BAR CHART               │  PIE / DONUT CHART             │
│  Top 10 Products         │  Revenue by Region             │
├──────────────────────────┼────────────────────────────────┤
│  TABLE                   │  HEATMAP                       │
│  Top Customers           │  Sales by Day × Hour           │
├──────────────────────────┴────────────────────────────────┤
│  TABLE: Country-wise Sales with Revenue Share %           │
└───────────────────────────────────────────────────────────┘
```

---

*Part of the Smart Retail Analytics & Recommendation Warehouse project.*
