# Phase 2: Project Setup & Planning Guide

**Project:** Smart Retail Analytics & Recommendation Warehouse

---

## 1. Project Folder Structure

```
smart-retail/
│
├── data/
│   ├── raw/                        # Original, untouched datasets
│   │   └── OnlineRetail.xlsx
│   ├── cleaned/                    # Post-cleaning datasets
│   │   └── online_retail_cleaned.csv
│   └── processed/                  # Feature-engineered / warehouse-ready
│       ├── fact_sales.csv
│       ├── dim_customer.csv
│       ├── dim_product.csv
│       └── dim_time.csv
│
├── notebooks/                      # Jupyter notebooks for EDA & experiments
│   ├── 01_data_cleaning.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_data_warehouse.ipynb
│   ├── 04_customer_segmentation.ipynb
│   ├── 05_market_basket_analysis.ipynb
│   ├── 06_recommendation_engine.ipynb
│   ├── 07_churn_prediction.ipynb
│   └── 08_sentiment_analysis.ipynb
│
├── src/                            # Production-grade Python modules
│   ├── __init__.py
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── extract.py              # Data loading utilities
│   │   ├── transform.py            # Cleaning & transformation logic
│   │   └── load.py                 # Warehouse loading logic
│   ├── warehouse/
│   │   ├── __init__.py
│   │   └── schema.py               # Star-schema definitions (SQLAlchemy)
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── segmentation.py         # RFM & clustering models
│   │   ├── basket_analysis.py      # Apriori / FP-Growth
│   │   ├── churn.py                # Churn prediction models
│   │   └── sentiment.py            # Review sentiment classifier
│   ├── recommender/
│   │   ├── __init__.py
│   │   ├── collaborative.py        # User-based & item-based CF
│   │   ├── content_based.py        # Content-based filtering
│   │   └── hybrid.py               # Hybrid recommendation engine
│   └── utils/
│       ├── __init__.py
│       └── helpers.py              # Shared utility functions
│
├── dashboard/                      # BI dashboard application
│   ├── app.py                      # Streamlit / Dash entry point
│   ├── pages/
│   │   ├── overview.py
│   │   ├── segmentation.py
│   │   ├── recommendations.py
│   │   └── basket_analysis.py
│   └── assets/
│       └── style.css
│
├── models/                         # Serialised trained models
│   ├── churn_model.pkl
│   ├── segmentation_model.pkl
│   └── recommender_model.pkl
│
├── reports/                        # Generated figures and reports
│   ├── figures/
│   └── evaluation/
│
├── tests/                          # Unit and integration tests
│   ├── test_etl.py
│   ├── test_segmentation.py
│   └── test_recommender.py
│
├── docs/                           # Project documentation
│   └── Problem_Definition_and_Requirement_Analysis.md
│
├── requirements.txt                # Python dependencies
├── setup.py                        # Package setup (optional)
├── .gitignore
└── README.md
```

---

## 2. Tools and Python Libraries

### 2.1 Core Environment

| Tool            | Purpose                  | Install                        |
|-----------------|--------------------------|--------------------------------|
| Python 3.10+    | Runtime                  | python.org / conda             |
| pip / conda     | Package manager          | Built-in                       |
| Jupyter Lab     | Notebook environment     | `pip install jupyterlab`       |
| Git             | Version control          | git-scm.com                    |
| VS Code         | IDE                      | code.visualstudio.com          |

### 2.2 Python Libraries

```
# ---------- Data Handling ----------
pandas>=2.0
numpy>=1.24
openpyxl                  # Read .xlsx files

# ---------- Database / Warehouse ----------
sqlalchemy>=2.0
sqlite3                   # Built-in (or use psycopg2 for PostgreSQL)

# ---------- Visualisation ----------
matplotlib>=3.7
seaborn>=0.12
plotly>=5.15

# ---------- Machine Learning ----------
scikit-learn>=1.3
scipy>=1.11

# ---------- Recommendation Engine ----------
surprise                  # scikit-surprise for collaborative filtering

# ---------- Market Basket Analysis ----------
mlxtend>=0.22            # Apriori & association rules

# ---------- NLP / Sentiment ----------
nltk>=3.8
textblob                  # Simple sentiment analysis
# (Optional) transformers  # Hugging Face for advanced NLP

# ---------- Dashboard ----------
streamlit>=1.28           # Interactive BI dashboards
# (Alternative) dash>=2.14

# ---------- Utilities ----------
joblib                    # Model serialisation
tqdm                      # Progress bars
python-dotenv             # Environment variables
```

**Single install command:**
```bash
pip install pandas numpy openpyxl sqlalchemy matplotlib seaborn plotly scikit-learn scipy scikit-surprise mlxtend nltk textblob streamlit joblib tqdm python-dotenv jupyterlab
```

---

## 3. Downloading and Loading the UCI Online Retail Dataset

### 3.1 About the Dataset
- **Name:** Online Retail Data Set
- **Source:** UCI Machine Learning Repository
- **URL:** https://archive.ics.uci.edu/ml/datasets/Online+Retail
- **Records:** ~541,909 transactions
- **Period:** 01/12/2010 – 09/12/2011
- **Columns:** InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country

### 3.2 Download Options

**Option A — Manual download:**
1. Visit: https://archive.ics.uci.edu/ml/machine-learning-databases/00352/
2. Download `Online Retail.xlsx`
3. Place in `data/raw/`

**Option B — Programmatic download (Python):**
```python
import urllib.request, os

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
os.makedirs("data/raw", exist_ok=True)
urllib.request.urlretrieve(url, "data/raw/OnlineRetail.xlsx")
print("Download complete.")
```

### 3.3 Loading the Dataset
```python
import pandas as pd

df = pd.read_excel("data/raw/OnlineRetail.xlsx", engine="openpyxl")
print(f"Shape: {df.shape}")
print(df.head())
print(df.info())
```

---

## 4. End-to-End Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        END-TO-END WORKFLOW                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHASE 1 ──► Data Acquisition & Cleaning                            │
│              • Download UCI Online Retail dataset                    │
│              • Remove nulls, duplicates, cancelled invoices          │
│              • Engineer TotalAmount column                           │
│              • Save cleaned CSV                                      │
│                                                                      │
│  PHASE 2 ──► Exploratory Data Analysis (EDA)                        │
│              • Univariate & bivariate analysis                       │
│              • Sales trends over time                                │
│              • Top products, countries, customers                    │
│              • Correlation heatmaps                                  │
│                                                                      │
│  PHASE 3 ──► Data Warehouse Design                                  │
│              • Design star schema (fact_sales + dimensions)          │
│              • Create dimension tables: customer, product, time      │
│              • Load into SQLite / PostgreSQL                         │
│              • Validate with OLAP queries                            │
│                                                                      │
│  PHASE 4 ──► Customer Segmentation                                  │
│              • Compute RFM scores                                    │
│              • Apply K-Means clustering (elbow method)               │
│              • Profile & label segments                              │
│              • Visualise clusters                                    │
│                                                                      │
│  PHASE 5 ──► Market Basket Analysis                                 │
│              • Build transaction matrix                              │
│              • Run Apriori / FP-Growth                               │
│              • Extract rules with support, confidence, lift          │
│              • Visualise top association rules                       │
│                                                                      │
│  PHASE 6 ──► Recommendation Engine                                  │
│              • User-based collaborative filtering                   │
│              • Item-based collaborative filtering                   │
│              • Content-based filtering (product attributes)         │
│              • Hybrid model + evaluation (Precision@K, NDCG)        │
│                                                                      │
│  PHASE 7 ──► Churn Prediction                                       │
│              • Feature engineering (recency, frequency, etc.)       │
│              • Train classifiers (Logistic Reg, Random Forest, XGB) │
│              • Evaluate (AUC-ROC, F1, confusion matrix)             │
│              • Generate at-risk customer list                       │
│                                                                      │
│  PHASE 8 ──► Sentiment Analysis (if review data available)          │
│              • Preprocess review text                                │
│              • Classify sentiment (positive/negative/neutral)       │
│              • Aggregate to product-level sentiment scores          │
│                                                                      │
│  PHASE 9 ──► BI Dashboard                                           │
│              • Build Streamlit / Dash multi-page app                │
│              • Integrate all analytics outputs                      │
│              • Add filters, drill-downs, KPI cards                  │
│              • Deploy locally or to cloud                           │
│                                                                      │
│  PHASE 10 ─► Documentation & Reporting                              │
│              • Write project report (academic format)               │
│              • Record demo video                                    │
│              • Prepare presentation                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Expected Outputs at Project Completion

| # | Deliverable                          | Format / Location                          |
|---|--------------------------------------|--------------------------------------------|
| 1 | Cleaned dataset                      | `data/cleaned/online_retail_cleaned.csv`   |
| 2 | EDA report with visualisations       | `notebooks/02_eda.ipynb` + `reports/figures/` |
| 3 | Star-schema data warehouse           | SQLite DB or PostgreSQL (+ ER diagram)     |
| 4 | Customer segments (4–6 clusters)     | Saved model + visualisation plots          |
| 5 | Market basket association rules      | Table of rules (support, confidence, lift) |
| 6 | Recommendation engine                | Trained model + Top-N output per user      |
| 7 | Churn prediction model               | Saved `.pkl` model + evaluation metrics    |
| 8 | Sentiment analysis results           | Product sentiment scores (CSV)             |
| 9 | Interactive BI dashboard             | Streamlit app (`dashboard/app.py`)         |
| 10| Project report                       | `docs/` folder (Word / PDF / Markdown)     |
| 11| requirements.txt                     | Root of project                            |
| 12| README with setup instructions       | Root of project                            |

---

*Phase 2 of the Smart Retail Analytics & Recommendation Warehouse project.*
