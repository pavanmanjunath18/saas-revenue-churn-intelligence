"""
Data quality tests for the SaaS Revenue & Churn Intelligence Platform.

Runs against the generated synthetic CSV files (no database required).
Execute: pytest tests/test_data_quality.py -v
"""
import pytest
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "synthetic"


def load(table: str) -> pd.DataFrame:
    path = DATA_DIR / f"{table}.csv"
    if not path.exists():
        pytest.skip(f"CSV not found: {path}. Run: python scripts/generate_mock_data.py")
    return pd.read_csv(path, low_memory=False)


# ── Existence and volume checks ───────────────────────────────────────────────

class TestFileExistence:
    EXPECTED_TABLES = [
        "products", "plans", "customers", "discounts",
        "subscriptions", "subscription_items",
        "invoices", "invoice_line_items",
        "payments", "refunds",
        "product_usage", "support_tickets",
    ]

    def test_all_csv_files_exist(self):
        for table in self.EXPECTED_TABLES:
            assert (DATA_DIR / f"{table}.csv").exists(), f"Missing: {table}.csv"

    def test_minimum_row_counts(self):
        expectations = {
            "customers":    1_400,
            "subscriptions": 2_000,
            "invoices":     8_000,
            "payments":     7_000,
            "product_usage": 10_000,
        }
        for table, min_rows in expectations.items():
            df = load(table)
            assert len(df) >= min_rows, (
                f"{table}: expected >= {min_rows} rows, got {len(df)}"
            )


# ── Schema / column checks ────────────────────────────────────────────────────

class TestCustomers:
    def test_required_columns_present(self):
        df = load("customers")
        required = {"customer_id", "company_name", "segment", "industry",
                    "signup_date", "is_deleted"}
        assert required.issubset(set(df.columns))

    def test_segments_valid(self):
        df = load("customers")
        valid = {"smb", "mid_market", "enterprise"}
        actual = set(df["segment"].dropna().unique())
        assert actual.issubset(valid), f"Unexpected segments: {actual - valid}"

    def test_no_duplicate_customer_ids(self):
        df = load("customers")
        assert df["customer_id"].nunique() == len(df), "Duplicate customer_id values found"

    def test_customer_count_in_range(self):
        df = load("customers")
        assert 1_400 <= len(df) <= 1_600, f"Unexpected customer count: {len(df)}"


class TestSubscriptions:
    def test_required_columns_present(self):
        df = load("subscriptions")
        required = {"subscription_id", "customer_id", "product_id",
                    "started_at", "status", "mrr_cents"}

        assert required.issubset(set(df.columns))

    def test_mrr_cents_non_negative(self):
        df = load("subscriptions")
        assert (df["mrr_cents"] >= 0).all(), "Negative mrr_cents found"

    def test_status_values_valid(self):
        df = load("subscriptions")
        valid = {"active", "canceled", "trialing", "past_due"}
        actual = set(df["status"].dropna().unique())
        assert actual.issubset(valid), f"Unexpected statuses: {actual - valid}"

    def test_canceled_at_after_started_at(self):
        df = load("subscriptions").dropna(subset=["canceled_at"])
        df["started_at"] = pd.to_datetime(df["started_at"])
        df["canceled_at"] = pd.to_datetime(df["canceled_at"])
        bad = df[df["canceled_at"] <= df["started_at"]]
        assert len(bad) == 0, f"{len(bad)} subscriptions have canceled_at <= started_at"


class TestInvoices:
    def test_required_columns_present(self):
        df = load("invoices")
        required = {"invoice_id", "customer_id", "subscription_id",
                    "total_cents", "status", "issued_at"}
        assert required.issubset(set(df.columns))

    def test_total_cents_non_negative(self):
        df = load("invoices")
        assert (df["total_cents"] >= 0).all(), "Negative invoice amounts found"

    def test_invoice_status_valid(self):
        df = load("invoices")
        valid = {"paid", "open", "void", "uncollectible"}
        actual = set(df["status"].dropna().unique())
        assert actual.issubset(valid), f"Unexpected invoice statuses: {actual - valid}"


class TestProductUsage:
    def test_required_columns_present(self):
        df = load("product_usage")
        required = {"customer_id", "month", "sessions_count",
                    "api_calls", "features_used_count"}
        assert required.issubset(set(df.columns))

    def test_counts_non_negative(self):
        df = load("product_usage")
        for col in ["sessions_count", "api_calls", "features_used_count"]:
            assert (df[col] >= 0).all(), f"Negative values in {col}"


class TestSupportTickets:
    def test_required_columns_present(self):
        df = load("support_tickets")
        required = {"ticket_id", "customer_id", "priority", "status", "opened_at"}
        assert required.issubset(set(df.columns))

    def test_priority_values_valid(self):
        df = load("support_tickets")
        valid = {"low", "medium", "high", "critical"}
        actual = set(df["priority"].dropna().unique())
        assert actual.issubset(valid), f"Unexpected priorities: {actual - valid}"


# ── Cross-table referential integrity ─────────────────────────────────────────

class TestReferentialIntegrity:
    def test_subscriptions_reference_valid_customers(self):
        customers = load("customers")
        subs = load("subscriptions")
        invalid = ~subs["customer_id"].isin(customers["customer_id"])
        assert invalid.sum() == 0, f"{invalid.sum()} subscriptions reference unknown customers"

    def test_invoices_reference_valid_customers(self):
        customers = load("customers")
        invoices = load("invoices")
        invalid = ~invoices["customer_id"].isin(customers["customer_id"])
        assert invalid.sum() == 0, f"{invalid.sum()} invoices reference unknown customers"

    def test_product_usage_references_valid_customers(self):
        customers = load("customers")
        usage = load("product_usage")
        invalid = ~usage["customer_id"].isin(customers["customer_id"])
        assert invalid.sum() == 0, f"{invalid.sum()} usage rows reference unknown customers"
