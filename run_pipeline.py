"""
Smart Retail Analytics — End-to-End Orchestration Pipeline
Executes data cleaning, warehouse construction, BI verification, customer segmentation,
and market basket analysis in the proper dependency order.
"""

import sys
import time
import argparse
import os

from data_cleaning import run_cleaning_pipeline, RAW_FILE, CLEANED_FILE
from build_warehouse import build_warehouse, DB_FILE, SCHEMA_FILE
from customer_segmentation import run_customer_segmentation
from market_basket_analysis import run_market_basket_analysis
from bi_queries import get_connection, get_kpis


def print_stage_banner(stage_num: int, title: str):
    """Format and print a prominent stage header."""
    print("\n" + "=" * 70)
    print(f"  STAGE {stage_num}: {title.upper()}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run Smart Retail Analytics Pipeline")
    parser.add_argument("--stage", choices=["all", "clean", "warehouse", "segmentation", "mba", "bi"], default="all",
                        help="Specific pipeline stage to run (default: all)")
    parser.add_argument("--skip-clean", action="store_true", help="Skip data cleaning if cleaned CSV exists")
    parser.add_argument("--force-rebuild", action="store_true", help="Force warehouse rebuild without backup prompt")

    args = parser.parse_args()
    start_time = time.time()
    generated_artifacts = []

    print("\n" + "#" * 70)
    print("  SMART RETAIL ANALYTICS & RECOMMENDATION WAREHOUSE")
    print("  Automated Pipeline Orchestrator")
    print("#" * 70)

    try:
        # STAGE 1: DATA CLEANING
        if args.stage in ("all", "clean"):
            print_stage_banner(1, "Data Acquisition & Cleaning ETL")
            if args.skip_clean and os.path.exists(CLEANED_FILE):
                print(f"Skipping data cleaning: {CLEANED_FILE} already exists.")
            else:
                run_cleaning_pipeline(RAW_FILE, CLEANED_FILE)
            if not os.path.exists(CLEANED_FILE):
                raise FileNotFoundError(f"Expected cleaned file {CLEANED_FILE} not found!")
            generated_artifacts.append(CLEANED_FILE)

        # STAGE 2: DATA WAREHOUSE CONSTRUCTION
        if args.stage in ("all", "warehouse"):
            print_stage_banner(2, "Star Schema Warehouse Builder (SQLite)")
            if not os.path.exists(CLEANED_FILE):
                raise FileNotFoundError(f"Prerequisite missing: {CLEANED_FILE} must exist before building warehouse.")
            stats = build_warehouse(
                cleaned_file=CLEANED_FILE,
                db_file=DB_FILE,
                schema_file=SCHEMA_FILE,
                force=args.force_rebuild,
                backup=True
            )
            generated_artifacts.append(DB_FILE)

        # STAGE 3: BUSINESS INTELLIGENCE & OLAP VALIDATION
        if args.stage in ("all", "bi"):
            print_stage_banner(3, "Warehouse BI Verification & OLAP Audit")
            if not os.path.exists(DB_FILE):
                raise FileNotFoundError(f"Prerequisite missing: {DB_FILE} does not exist.")
            conn = get_connection(DB_FILE)
            kpis = get_kpis(conn)
            conn.close()
            print("  Core Warehouse KPIs Verified:")
            print(f"    - Gross Revenue:     £{kpis['GrossRevenue']:,.2f}")
            print(f"    - Total Orders:      {kpis['TotalOrders']:,}")
            print(f"    - Unique Customers:  {kpis['UniqueCustomers']:,}")
            print(f"    - Unique Products:   {kpis['UniqueProducts']:,}")
            print(f"    - Total Units Sold:  {kpis['TotalUnitsSold']:,}")
            print(f"    - Average Order Val: £{kpis['AvgOrderValue']:,.2f}")

        # STAGE 4: CUSTOMER SEGMENTATION (RFM + K-MEANS)
        if args.stage in ("all", "segmentation"):
            print_stage_banner(4, "Customer Segmentation (RFM + K-Means Clustering)")
            if not os.path.exists(CLEANED_FILE):
                raise FileNotFoundError(f"Prerequisite missing: {CLEANED_FILE} not found.")
            seg_results = run_customer_segmentation(CLEANED_FILE)
            generated_artifacts.extend([
                "data/processed/customer_segments.csv",
                "data/processed/clustering_validation.json",
                "data/processed/segmentation_results.txt",
                "reports/figures/elbow_silhouette.png"
            ])

        # STAGE 5: MARKET BASKET ANALYSIS (APRIORI)
        if args.stage in ("all", "mba"):
            print_stage_banner(5, "Market Basket Analysis (Apriori Association Rules)")
            if not os.path.exists(CLEANED_FILE):
                raise FileNotFoundError(f"Prerequisite missing: {CLEANED_FILE} not found.")
            mba_results = run_market_basket_analysis(CLEANED_FILE)
            generated_artifacts.extend([
                "data/processed/association_rules.csv",
                "data/processed/frequent_itemsets.csv",
                "data/processed/mba_summary.json",
                "data/processed/mba_results.txt"
            ])

        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print("  PIPELINE EXECUTION SUCCESSFUL")
        print("=" * 70)
        print(f"Total execution time: {elapsed:.2f} seconds")
        print("\nGenerated & Verified Artifacts:")
        for path in set(generated_artifacts):
            if os.path.exists(path):
                size_kb = os.path.getsize(path) / 1024
                print(f"  [✓] {path:<40s} ({size_kb:,.1f} KB)")
        print("\nReady to launch dashboard: streamlit run dashboard/app.py\n")
        return 0

    except Exception as e:
        print("\n" + "!" * 70, file=sys.stderr)
        print(f"  PIPELINE EXECUTION FAILED: {e}", file=sys.stderr)
        print("!" * 70 + "\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
