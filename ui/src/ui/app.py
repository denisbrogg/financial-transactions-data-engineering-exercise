import os
from pathlib import Path

import duckdb
import streamlit as st

DATABASE_PATH = Path(os.getenv("DATA_ROOT", "/data")) / "db" / "transactions.duckdb"

st.set_page_config(page_title="Transactions", page_icon=":bar_chart:")
st.title("Transactions")

if not DATABASE_PATH.exists():
    st.error(f"Database not found: {DATABASE_PATH}")
    st.stop()

with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
    tables = connection.execute("SHOW TABLES").fetchall()

if not tables:
    st.info("The database does not contain any tables yet.")
    st.stop()

table_name = st.selectbox("Table", [table[0] for table in tables])

with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
    data = connection.execute(
        f'SELECT * FROM "{table_name.replace(chr(34), chr(34) * 2)}"'
    ).fetchdf()

st.dataframe(data, use_container_width=True, hide_index=True)
