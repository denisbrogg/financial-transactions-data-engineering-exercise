import math
import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = (
    Path(os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data")))
    / "db"
    / "transactions.duckdb"
)


def require_db() -> None:
    if not DATABASE_PATH.exists():
        st.error(f"Database not found at: {DATABASE_PATH}")
        st.stop()


@st.cache_data(show_spinner=False)
def fetch_df(query: str, params: tuple | None = None) -> "pd.DataFrame":
    params = params or ()
    with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
        return connection.execute(query, params).fetchdf()


def format_number(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "0"
    if isinstance(value, int):
        return f"{value:,}".replace(",", "'")
    return f"{float(value):,.0f}".replace(",", "'")


def format_currency(value, decimals: int = 2):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "CHF 0.00"
    formatted = f"{float(value):,.{decimals}f}".replace(",", "'")
    return f"CHF {formatted}"


def money(value):
    return format_currency(value)


def currency_warning() -> None:
    st.warning(
        "Warning: currency conversion is not yet applied; figures are displayed in CHF without FX adjustment.",
        icon="⚠️",
    )
