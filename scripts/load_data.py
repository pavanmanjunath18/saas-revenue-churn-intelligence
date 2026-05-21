#!/usr/bin/env python3
"""
SaaS Revenue & Churn Intelligence Platform — Phase 2
CSV → PostgreSQL Loader

Loads all 12 generated CSV files into the `raw` schema.
Explicitly converts all numpy/pandas types to native Python types so
psycopg2 maps them correctly to PostgreSQL column types.

Usage:
    cp .env.example .env        # fill in credentials if needed
    python scripts/load_data.py
"""

import os, sys, time, math
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://saas_user:saas_pass@localhost:5433/saas_platform",
)
DATA_DIR = Path(__file__).parent.parent / "data" / "synthetic"

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; E = "\033[0m"

# ── FK load order ──────────────────────────────────────────────────────────
LOAD_ORDER = [
    "products", "plans", "customers", "discounts",
    "subscriptions", "subscription_items",
    "invoices", "invoice_line_items",
    "payments", "refunds",
    "product_usage", "support_tickets",
]

BOOL_COLS  = {"is_active", "is_deleted"}
DATE_COLS  = {
    "signup_date", "started_at", "canceled_at", "trial_ends_at",
    "valid_from", "valid_until", "billing_period_start",
    "billing_period_end", "month", "ended_at",
}
TS_COLS    = {
    "created_at", "updated_at", "issued_at", "due_at", "paid_at",
    "attempted_at", "opened_at", "resolved_at",
}

BATCH_SIZE = 500


def _to_py(col: str, val):
    """
    Convert a single pandas/numpy value to a native Python type.
    Returns None for NaN, NaT, or missing values.
    """
    # Null detection — covers float NaN, numpy NaN, pandas NaT, Python None
    if val is None:
        return None
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, float) and val != val:   # NaN check (NaN != NaN)
        return None

    # numpy scalar types → Python native
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return None if math.isnan(float(val)) else float(val)
    if isinstance(val, np.bool_):
        return bool(val)

    # Boolean columns (CSV stores as string "True"/"False" or Python bool)
    if col in BOOL_COLS:
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() == "true"

    # Date columns — keep as ISO date string, strip time component
    if col in DATE_COLS:
        s = str(val).split("T")[0].split(" ")[0]
        return s if s and s != "nan" and s != "None" else None

    # Timestamp columns — convert to UTC-aware string psycopg2 understands
    if col in TS_COLS:
        s = str(val).replace("T", " ").replace("Z", "+00:00")
        return s if s and "nan" not in s and "None" not in s else None

    return val


def df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[tuple]]:
    """Return (columns, list_of_row_tuples) with all values as native Python types."""
    cols = list(df.columns)
    rows = []
    for record in df.to_dict(orient="records"):
        rows.append(tuple(_to_py(col, record[col]) for col in cols))
    return cols, rows


def insert_table(cur, table: str, df: pd.DataFrame) -> int:
    cols, rows = df_to_rows(df)
    col_str = ", ".join(f'"{c}"' for c in cols)
    sql     = (f'INSERT INTO raw."{table}" ({col_str}) VALUES %s '
               f'ON CONFLICT DO NOTHING')
    total   = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        psycopg2.extras.execute_values(cur, sql, batch, page_size=BATCH_SIZE)
        total += len(batch)
    return total


def main():
    print(f"\n{Y}SaaS Platform — Phase 2 Data Loader{E}")
    print(f"  Target:   {DATABASE_URL.split('@')[-1]}")
    print(f"  Data dir: {DATA_DIR}\n")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur  = conn.cursor()
        print(f"{G}Connected to PostgreSQL{E}\n")
    except Exception as e:
        print(f"{R}Connection failed: {e}{E}")
        print("  Is Docker running?  docker compose up -d")
        sys.exit(1)

    results    = []
    total_rows = 0

    for table in LOAD_ORDER:
        csv_path = DATA_DIR / f"{table}.csv"
        if not csv_path.exists():
            print(f"  {R}MISS{E}   {table:<25}  file not found")
            results.append((table, False, 0))
            continue

        try:
            df      = pd.read_csv(csv_path, low_memory=False)
            t0      = time.time()
            n       = insert_table(cur, table, df)
            conn.commit()
            elapsed = time.time() - t0
            total_rows += n
            print(f"  {G}OK{E}    {table:<25}  {n:>7,} rows  ({elapsed:.2f}s)")
            results.append((table, True, n))
        except Exception as e:
            conn.rollback()
            print(f"  {R}FAIL{E}  {table:<25}  {e}")
            results.append((table, False, 0))

    cur.close()
    conn.close()

    failed = [t for t, ok, _ in results if not ok]
    print(f"\n{'─'*52}")
    print(f"  Total rows loaded: {total_rows:,}")
    if failed:
        print(f"\n  {R}Failed: {', '.join(failed)}{E}")
        sys.exit(1)
    else:
        print(f"\n  {G}All 12 tables loaded successfully.{E}")
        print("  Run:  psql $DATABASE_URL -f sql/schema/03_validation_queries.sql")


if __name__ == "__main__":
    main()
