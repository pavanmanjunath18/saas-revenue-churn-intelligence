#!/usr/bin/env bash
# =============================================================================
# setup_cloud_db.sh
#
# One-command setup: generates synthetic data, loads raw tables, and builds
# all 8 analytics models against any PostgreSQL URL (local or cloud).
#
# Usage:
#   export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
#   bash scripts/setup_cloud_db.sh
#
# Or inline:
#   DATABASE_URL="postgresql://..." bash scripts/setup_cloud_db.sh
#
# Requires: psql, python3, pip
# =============================================================================
set -euo pipefail

G="\033[92m"; R="\033[91m"; Y="\033[93m"; B="\033[94m"; E="\033[0m"

echo -e "\n${B}================================================${E}"
echo -e "${B}  SaaS Revenue & Churn Intelligence — DB Setup ${E}"
echo -e "${B}================================================${E}\n"

# ── Validate DATABASE_URL ─────────────────────────────────────────────────────
if [[ -z "${DATABASE_URL:-}" ]]; then
  # Try .env fallback
  if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo -e "${R}ERROR: DATABASE_URL is not set.${E}"
  echo ""
  echo "  Set it before running:"
  echo "    export DATABASE_URL=\"postgresql://user:pass@host/db?sslmode=require\""
  echo ""
  echo "  Or copy .env.example to .env and fill it in."
  exit 1
fi

# Mask credentials in display
DISPLAY_URL=$(echo "$DATABASE_URL" | sed 's|://[^@]*@|://***:***@|')
echo -e "  Target: ${Y}${DISPLAY_URL}${E}\n"

# ── Step 1: Install Python dependencies ──────────────────────────────────────
echo -e "${B}[1/5] Installing Python dependencies...${E}"
pip install -q -r requirements.txt
echo -e "${G}      Done.${E}\n"

# ── Step 2: Generate synthetic data ──────────────────────────────────────────
echo -e "${B}[2/5] Generating synthetic data (1,500 customers, 24 months)...${E}"
python3 scripts/generate_mock_data.py
echo -e "${G}      Done.${E}\n"

# ── Step 3: Create raw schema & tables ───────────────────────────────────────
echo -e "${B}[3/5] Creating raw schema and tables...${E}"
psql "$DATABASE_URL" -f sql/schema/01_create_schema.sql -q
echo -e "${G}      Done.${E}\n"

# ── Step 4: Load CSV data into raw tables ────────────────────────────────────
echo -e "${B}[4/5] Loading CSV data into PostgreSQL...${E}"
python3 scripts/load_data.py
echo -e "${G}      Done.${E}\n"

# ── Step 5: Build analytics layer ────────────────────────────────────────────
echo -e "${B}[5/5] Building 8 analytics models (SQL)...${E}"
psql "$DATABASE_URL" -f sql/analytics/99_run_all_analytics.sql -q
echo -e "${G}      Done.${E}\n"

echo -e "${G}================================================${E}"
echo -e "${G}  Setup complete! Database is ready.${E}"
echo -e "${G}================================================${E}"
echo ""
echo "  Next steps:"
echo "  1. Copy DATABASE_URL into Streamlit Cloud secrets:"
echo "     App Settings → Secrets → add:  DATABASE_URL = \"...\""
echo "  2. Redeploy the app."
echo ""
