import sys
from pathlib import Path

import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import fetch_df, require_db


def main():
    require_db()
    st.title("Customers")

    customer_metrics = fetch_df(
        """
        SELECT
            COALESCE(c.client_name, 'Unknown') AS client_name,
            COUNT(*) AS transactions,
            ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount,
            ROUND(CAST(SUM(t.fee) AS DOUBLE), 2) AS fees
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_clients c ON c.client_id = t.client_id
        GROUP BY COALESCE(c.client_name, 'Unknown')
        ORDER BY transactions DESC, gross_amount DESC
        LIMIT 10
        """
    )

    customer_by_fee = customer_metrics.sort_values("fees", ascending=False).reset_index(
        drop=True
    )

    st.subheader("Most active customers by transaction count")
    st.dataframe(
        customer_metrics,
        width="stretch",
        hide_index=True,
        column_config={
            "client_name": st.column_config.TextColumn("Client"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "gross_amount": st.column_config.NumberColumn(
                "Gross amount", format="€%.2f"
            ),
            "fees": st.column_config.NumberColumn("Fees", format="€%.2f"),
        },
    )
    st.caption(
        "Business question: Which customers are the most active, and who is driving daily trading intensity?"
    )

    st.subheader("Best customers by fee")
    st.dataframe(
        customer_by_fee[["client_name", "transactions", "gross_amount", "fees"]],
        width="stretch",
        hide_index=True,
        column_config={
            "client_name": st.column_config.TextColumn("Client"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "gross_amount": st.column_config.NumberColumn(
                "Gross amount", format="€%.2f"
            ),
            "fees": st.column_config.NumberColumn("Fees", format="€%.2f"),
        },
    )
    st.caption(
        "Business question: Which customers are contributing the most fee revenue and where is value concentrated?"
    )
    st.caption(
        "This section is designed for ranked leaderboards and customer concentration analysis."
    )

    st.caption(
        "Next step: add customer-level trend lines and customer segmentation by risk profile or country."
    )


if __name__ == "__main__":
    main()
