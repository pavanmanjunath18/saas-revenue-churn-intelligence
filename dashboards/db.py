"""Database connection and cached query helpers.

Connection priority (highest → lowest):
  1. Streamlit Cloud secrets  → st.secrets["DATABASE_URL"]
  2. Local .env file          → DATABASE_URL=...
  3. Hard-coded default       → localhost:5433 (dev only)
"""
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


def _get_db_url() -> str:
    # 1. Streamlit Cloud / secrets.toml
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, AttributeError, FileNotFoundError):
        pass

    # 2. .env file (local dev)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    except ImportError:
        pass

    return os.getenv(
        "DATABASE_URL",
        "postgresql://saas_user:saas_pass@localhost:5433/saas_platform",
    )


@st.cache_resource
def _get_engine():
    """Create the SQLAlchemy engine once and reuse it."""
    return create_engine(_get_db_url(), pool_pre_ping=True)


@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    with _get_engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn)
