# Database Setup — SaaS Revenue & Churn Intelligence Platform

## Overview

PostgreSQL 15 running in Docker.  
Schema: `raw` (12 tables, 50K rows, ~8MB).  
All setup is a one-time operation — once the data is loaded you can query freely.

---

## Prerequisites

- Docker Desktop installed and running
- Python 3.10+ with pip
- psql (optional, for running SQL files directly)

---

## Step 1 — Install Python dependencies

```bash
pip install psycopg2-binary pandas python-dotenv faker numpy
```

---

## Step 2 — Configure credentials

```bash
cp .env.example .env
```

Default `.env` values work out of the box. Only change them if port 5433 is already in use on your machine.

```
POSTGRES_USER=saas_user
POSTGRES_PASSWORD=saas_pass
POSTGRES_DB=saas_platform
POSTGRES_PORT=5433
DATABASE_URL=postgresql://saas_user:saas_pass@localhost:5433/saas_platform
```

> **Note:** Port `5433` is used (not the default 5432) to avoid conflicts with any locally installed PostgreSQL.

---

## Step 3 — Start PostgreSQL

```bash
docker compose up -d
```

Verify it is healthy:

```bash
docker compose ps
# Status should show "healthy"
```

---

## Step 4 — Generate synthetic data (if not already done)

```bash
python scripts/generate_mock_data.py
# Outputs 12 CSV files to data/synthetic/
```

---

## Step 5 — Create schema

```bash
# Option A: via Docker (no local psql needed)
docker exec -i saas-platform-postgres-1 \
  psql -U saas_user -d saas_platform \
  < sql/schema/01_create_schema.sql

# Option B: via local psql
psql $DATABASE_URL -f sql/schema/01_create_schema.sql
```

This creates the `raw` schema and all 12 tables with PKs, FKs, and indexes.

---

## Step 6 — Load data

```bash
python scripts/load_data.py
```

Expected output:
```
OK    products                     2 rows
OK    plans                       10 rows
OK    customers                1,500 rows
OK    discounts                  394 rows
OK    subscriptions            2,394 rows
OK    subscription_items         305 rows
OK    invoices                10,495 rows
OK    invoice_line_items      10,495 rows
OK    payments                 9,120 rows
OK    refunds                    157 rows
OK    product_usage           12,256 rows
OK    support_tickets          2,908 rows

Total rows loaded: 50,036
All 12 tables loaded successfully.
```

---

## Step 7 — Run validation queries

```bash
# Option A: via Docker
docker exec -i saas-platform-postgres-1 \
  psql -U saas_user -d saas_platform \
  < sql/schema/03_validation_queries.sql

# Option B: via local psql
psql $DATABASE_URL -f sql/schema/03_validation_queries.sql
```

All FK integrity checks should return `0` rows.
Business sanity stats will show MRR, segment breakdown, and invoice payment rates.

---

## Connecting with a SQL client

Use any PostgreSQL-compatible client (DBeaver, TablePlus, DataGrip):

| Field    | Value         |
|----------|---------------|
| Host     | localhost     |
| Port     | 5433          |
| Database | saas_platform |
| User     | saas_user     |
| Password | saas_pass     |

---

## Resetting and reloading

To wipe all data and reload from scratch:

```bash
# Drop and recreate schema
docker exec -i saas-platform-postgres-1 \
  psql -U saas_user -d saas_platform \
  < sql/schema/01_create_schema.sql

# Reload
python scripts/load_data.py
```

To fully reset the Docker volume:

```bash
docker compose down -v
docker compose up -d
# Then repeat steps 5 and 6
```

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` | Docker not running | `docker compose up -d` |
| `port already allocated` | Port 5433 in use | Change `POSTGRES_PORT` in `.env` and `docker-compose.yml` |
| `FK constraint violation` | Loading in wrong order | Let `load_data.py` handle order — don't load tables manually |
| `ON CONFLICT DO NOTHING` silent skip | Duplicate PK/unique value | Re-run generator to get fresh data; always reset schema before loading |
| `invalid value encountered` | numpy NaN not converted | Handled by loader — if it reappears, check for new columns |

---

## Schema overview

All tables live in the `raw` schema.

```sql
-- List all tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'raw'
ORDER BY table_name;

-- Check row counts
SELECT schemaname, tablename, n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'raw'
ORDER BY row_count DESC;
```

---

---

## Step 8 — Build the Analytics Layer

Now that the raw data is fully loaded and validated, compile the `analytics` schema using the automated schema compiler.

This python script acts as an analytics database compiler, automatically establishing the `analytics` schema, dropping stale assets to avoid dependency collisions, and executing all models in their correct structural dependency order:

```bash
python scripts/build_analytics.py
```

### Expected Compiler Output:
```
SaaS Platform — Analytics Layer Compiler
  Target DB: localhost:5433/saas_platform

Connected to PostgreSQL

  OK    Created schema 'analytics'

  Cleaning existing views/materialized views...
  Cleaned.

  OK    01_customer_overview.sql             (0.01s)
  OK    02_subscription_details.sql          (0.01s)
  OK    03_invoice_details.sql               (0.01s)
  OK    05_mrr_movement_report.sql           (0.72s)
  OK    04_monthly_revenue_overview.sql      (0.02s)
  OK    06_cohort_retention.sql              (0.04s)
  OK    07_customer_health_scores.sql        (0.05s)
  OK    08_churn_risk_segments.sql           (0.02s)

──────────────────────────────────────────────────
  Analytics Schema Compilation Complete!
──────────────────────────────────────────────────

  mrr_movement_report            12,607 rows
  monthly_revenue_overview           24 rows
  cohort_retention                  300 rows
  customer_health_scores          1,108 rows
  churn_risk_segments             1,108 rows
```

All analytical models are now materialised and ready to be queried or visualised in the Streamlit application!

---

## What's next

Proceed to the [Analytics Layer Guide](analytics_layer.md) to understand the underlying SQL transformations, the MRR state machine, and customer health algorithms.

