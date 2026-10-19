# Smart Retail Analytics & Recommendation Warehouse

> E-commerce Customer Intelligence System — Final Year Engineering Project

## Overview

An end-to-end retail analytics platform that combines **data warehousing**, **customer segmentation**, **market basket analysis**, **recommendation engines**, and **interactive BI dashboards** to derive actionable business intelligence from e-commerce transaction data.

**Dataset:** [UCI Online Retail Dataset](https://archive.ics.uci.edu/ml/datasets/Online+Retail) (~541K transactions, Dec 2010 – Dec 2011)

## Project Structure

```
smart-retail/
├── data/
│   ├── raw/                    # Original dataset (auto-downloaded)
│   ├── cleaned/                # Post-cleaning CSV
│   └── processed/              # Warehouse DB, segments, rules
├── reports/figures/            # Visualization plots
├── data_cleaning.py            # ETL — cleaning pipeline
├── build_warehouse.py          # Star schema warehouse builder
├── bi_queries.py               # 15+ OLAP analytical queries
├── market_basket_analysis.py   # Apriori association rules
├── customer_segmentation.py    # RFM + K-Means clustering
├── warehouse_schema.sql        # Star schema DDL
├── requirements.txt            # Python dependencies
└── docs/                       # Project documentation
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Clean the dataset (auto-downloads UCI data)
python data_cleaning.py

# 3. Build the star schema warehouse
python build_warehouse.py

# 4. Run BI analytical queries
python bi_queries.py

# 5. Market basket analysis (Apriori)
python market_basket_analysis.py

# 6. Customer segmentation (RFM + K-Means)
python customer_segmentation.py
```

## Key Results

| Module | Highlight |
|---|---|
| **Data Warehouse** | Star schema — 392K facts, 4 dimensions |
| **BI Queries** | 15+ OLAP queries (drill-down, roll-up, slice, dice) |
| **Market Basket** | 68 association rules, max lift = 24.0× |
| **Customer Segments** | 4 K-Means clusters + RFM scoring (4,338 customers) |

## Tech Stack

- **Language:** Python 3.10+
- **Data:** Pandas, NumPy, OpenPyXL
- **Database:** SQLite (star schema)
- **ML:** Scikit-learn, SciPy, mlxtend
- **Visualization:** Matplotlib, Seaborn
- **Dashboard:** Streamlit (upcoming)

## License

This project is developed for academic purposes as part of a final-year engineering project.
