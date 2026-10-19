-- ============================================================
-- SMART RETAIL ANALYTICS — STAR SCHEMA (SQLite compatible)
-- ============================================================
--
--              ┌──────────────┐
--              │  Dim_Time    │
--              └──────┬───────┘
--                     │
--  ┌──────────────┐   │   ┌──────────────┐
--  │ Dim_Customer ├───┤───┤ Dim_Product  │
--  └──────────────┘   │   └──────────────┘
--                     │
--              ┌──────┴───────┐
--              │  Fact_Sales  │
--              └──────┬───────┘
--                     │
--              ┌──────┴───────┐
--              │  Dim_Region  │
--              └──────────────┘
--

-- ============================================================
-- 1. DIMENSION: Dim_Time
-- ============================================================
-- Grain: one row per unique calendar date

CREATE TABLE IF NOT EXISTS Dim_Time (
    TimeKey         INTEGER PRIMARY KEY,    -- surrogate key (YYYYMMDD)
    FullDate        DATE        NOT NULL,
    Year            INTEGER     NOT NULL,
    Quarter         INTEGER     NOT NULL,   -- 1-4
    Month           INTEGER     NOT NULL,   -- 1-12
    MonthName       TEXT        NOT NULL,   -- 'January', ...
    Week            INTEGER     NOT NULL,   -- ISO week number
    DayOfMonth      INTEGER     NOT NULL,
    DayOfWeek       INTEGER     NOT NULL,   -- 0=Monday ... 6=Sunday
    DayName         TEXT        NOT NULL,   -- 'Monday', ...
    IsWeekend       INTEGER     NOT NULL    -- 0 or 1
);

-- ============================================================
-- 2. DIMENSION: Dim_Customer
-- ============================================================
-- Grain: one row per unique CustomerID

CREATE TABLE IF NOT EXISTS Dim_Customer (
    CustomerKey     INTEGER PRIMARY KEY,    -- surrogate key (auto)
    CustomerID      INTEGER     NOT NULL UNIQUE,
    FirstPurchase   DATE,
    LastPurchase    DATE,
    TotalOrders     INTEGER,
    TotalSpend      REAL,
    Country         TEXT                    -- most frequent country
);

-- ============================================================
-- 3. DIMENSION: Dim_Product
-- ============================================================
-- Grain: one row per unique StockCode

CREATE TABLE IF NOT EXISTS Dim_Product (
    ProductKey      INTEGER PRIMARY KEY,    -- surrogate key (auto)
    StockCode       TEXT        NOT NULL UNIQUE,
    Description     TEXT,
    AvgUnitPrice    REAL,
    TimesOrdered    INTEGER
);

-- ============================================================
-- 4. DIMENSION: Dim_Region
-- ============================================================
-- Grain: one row per unique Country

CREATE TABLE IF NOT EXISTS Dim_Region (
    RegionKey       INTEGER PRIMARY KEY,    -- surrogate key (auto)
    Country         TEXT        NOT NULL UNIQUE,
    Region          TEXT                    -- continent/grouping
);

-- ============================================================
-- 5. FACT TABLE: Fact_Sales
-- ============================================================
-- Grain: one row per invoice line item

CREATE TABLE IF NOT EXISTS Fact_Sales (
    SalesKey        INTEGER PRIMARY KEY AUTOINCREMENT,
    InvoiceNo       TEXT        NOT NULL,
    TimeKey         INTEGER     NOT NULL,
    CustomerKey     INTEGER     NOT NULL,
    ProductKey      INTEGER     NOT NULL,
    RegionKey       INTEGER     NOT NULL,
    Quantity        INTEGER     NOT NULL,
    UnitPrice       REAL        NOT NULL,
    TotalAmount     REAL        NOT NULL,
    InvoiceTime     TEXT,                   -- HH:MM:SS for intra-day analysis

    FOREIGN KEY (TimeKey)       REFERENCES Dim_Time(TimeKey),
    FOREIGN KEY (CustomerKey)   REFERENCES Dim_Customer(CustomerKey),
    FOREIGN KEY (ProductKey)    REFERENCES Dim_Product(ProductKey),
    FOREIGN KEY (RegionKey)     REFERENCES Dim_Region(RegionKey)
);

-- ============================================================
-- INDEXES for query performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_time      ON Fact_Sales(TimeKey);
CREATE INDEX IF NOT EXISTS idx_fact_customer  ON Fact_Sales(CustomerKey);
CREATE INDEX IF NOT EXISTS idx_fact_product   ON Fact_Sales(ProductKey);
CREATE INDEX IF NOT EXISTS idx_fact_region    ON Fact_Sales(RegionKey);
CREATE INDEX IF NOT EXISTS idx_fact_invoice   ON Fact_Sales(InvoiceNo);
