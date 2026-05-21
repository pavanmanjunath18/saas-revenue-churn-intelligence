#!/usr/bin/env python3
"""
SaaS Revenue & Churn Intelligence Platform — Phase 3
SQL Analytics Schema Compiler

Reads all SQL analytics models from sql/analytics/ and executes them
in dependency order on the target PostgreSQL database.

Usage:
    python scripts/build_analytics.py
"""

import os, sys, time
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://saas_user:saas_pass@localhost:5433/saas_platform",
)

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[96m"; E = "\033[0m"

# Dependency order for building the analytics layer
MODELS = [
    "01_customer_overview.sql",
    "02_subscription_details.sql",
    "03_invoice_details.sql",
    "05_mrr_movement_report.sql",
    "04_monthly_revenue_overview.sql",
    "06_cohort_retention.sql",
    "07_customer_health_scores.sql",
    "08_churn_risk_segments.sql",
]

def main():
    print(f"\n{Y}SaaS Platform — Analytics Layer Compiler{E}")
    print(f"  Target DB: {DATABASE_URL.split('@')[-1]}\n")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        print(f"{G}Connected to PostgreSQL{E}\n")
    except Exception as e:
        print(f"{R}Connection failed: {e}{E}")
        print("  Please check that your PostgreSQL database is running.")
        sys.exit(1)

    # 1. Create analytics schema
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
        print(f"  {G}OK{E}    Created schema 'analytics'")
    except Exception as e:
        print(f"  {R}FAIL{E}  Failed to create schema 'analytics': {e}")
        sys.exit(1)

    # 2. Safely drop existing views to avoid conflicts when recreating
    print(f"\n  Cleaning existing views/materialized views...")
    drops = [
        "DROP MATERIALIZED VIEW IF EXISTS analytics.churn_risk_segments CASCADE;",
        "DROP MATERIALIZED VIEW IF EXISTS analytics.customer_health_scores CASCADE;",
        "DROP MATERIALIZED VIEW IF EXISTS analytics.cohort_retention CASCADE;",
        "DROP MATERIALIZED VIEW IF EXISTS analytics.monthly_revenue_overview CASCADE;",
        "DROP MATERIALIZED VIEW IF EXISTS analytics.mrr_movement_report CASCADE;",
        "DROP VIEW IF EXISTS analytics.invoice_details CASCADE;",
        "DROP VIEW IF EXISTS analytics.subscription_details CASCADE;",
        "DROP VIEW IF EXISTS analytics.customer_overview CASCADE;"
    ]
    for d in drops:
        try:
            cur.execute(d)
        except Exception as e:
            pass
    print(f"  {G}Cleaned.{E}\n")

    # 3. Compile and execute models in order
    sql_dir = Path(__file__).parent.parent / "sql" / "analytics"

    for model in MODELS:
        file_path = sql_dir / model
        if not file_path.exists():
            print(f"  {R}MISS{E}   {model:<35}  file not found")
            sys.exit(1)

        try:
            t0 = time.time()
            sql_content = file_path.read_text()
            # PostgreSQL requires executing DDL statements
            cur.execute(sql_content)
            elapsed = time.time() - t0
            print(f"  {G}OK{E}    {model:<35}  ({elapsed:.2f}s)")
        except Exception as e:
            print(f"  {R}FAIL{E}  {model:<35}  {e}")
            sys.exit(1)

    # 4. Show build verification summary
    print(f"\n{B}{'─'*50}{E}")
    print(f"  {B}Analytics Schema Compilation Complete!{E}")
    print(f"{B}{'─'*50}{E}\n")

    # Query row counts
    models_to_query = [
        ("mrr_movement_report", "analytics.mrr_movement_report"),
        ("monthly_revenue_overview", "analytics.monthly_revenue_overview"),
        ("cohort_retention", "analytics.cohort_retention"),
        ("customer_health_scores", "analytics.customer_health_scores"),
        ("churn_risk_segments", "analytics.churn_risk_segments"),
    ]

    for label, table in models_to_query:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"  {label:<30} {count:>8,} rows")
        except Exception as e:
            print(f"  {label:<30}  Query failed: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
