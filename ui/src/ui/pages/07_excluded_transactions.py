import sys
from pathlib import Path

import pandas as pd
import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import fetch_df, fmt_chf, require_db


@st.cache_data(ttl=3600, show_spinner=False)
def load_flagged_transactions() -> pd.DataFrame:
    return fetch_df(
        """
        SELECT
            t.transaction_id,
            t.transaction_date,
            COALESCE(dcl.client_name, 'Unknown') AS client_name,
            COALESCE(dc.channel_name, 'Unknown') AS channel,
            COALESCE(dtt.transaction_type_name, 'Unknown') AS transaction_type,
            t.currency,
            t.gross_amount,
            t.fee,
            t.net_amount,
            t.notes,
            t.is_flagged
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_clients dcl ON dcl.client_id = t.client_id
        LEFT JOIN gold.dim_channels dc ON dc.channel_id = t.channel_id
        LEFT JOIN gold.dim_transaction_types dtt ON dtt.transaction_type_id = t.transaction_type_id
        WHERE COALESCE(t.is_flagged, FALSE) = TRUE
        ORDER BY t.transaction_date DESC, t.transaction_id
        """
    )


def main():
    require_db()
    st.title("Excluded flagged transactions")
    st.caption(
        "Transactions excluded from the KPI view because they are marked as flagged and require review."
    )

    df = load_flagged_transactions()

    if df.empty:
        st.info("No flagged transactions are currently present in the gold layer.")
        return

    total_value = float(df["gross_amount"].fillna(0).sum())
    total_fee = float(df["fee"].fillna(0).sum())
    count = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Flagged transactions", str(count))
    col2.metric("Gross value", fmt_chf(total_value, 2))
    col3.metric("Fees", fmt_chf(total_fee, 2))

    display = df.copy()
    display["gross_amount"] = display["gross_amount"].map(
        lambda v: fmt_chf(v, 2) if pd.notna(v) else "CHF —"
    )
    display["fee"] = display["fee"].map(
        lambda v: fmt_chf(v, 2) if pd.notna(v) else "CHF —"
    )
    display["net_amount"] = display["net_amount"].map(
        lambda v: fmt_chf(v, 2) if pd.notna(v) else "CHF —"
    )
    display = display.drop(columns=["is_flagged"])

    st.subheader("Flagged records")
    st.dataframe(display, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
