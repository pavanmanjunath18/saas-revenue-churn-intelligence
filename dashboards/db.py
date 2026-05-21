"""Database connection and cached query helpers."""
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://saas_user:saas_pass@localhost:5433/saas_platform",
)

_engine = create_engine(DB_URL)


@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    with _engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn)
