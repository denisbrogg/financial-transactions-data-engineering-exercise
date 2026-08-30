import sys
from pathlib import Path

import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import (
    currency_warning,
    fetch_df,
    format_number,
    money,
    require_db,
)


def main():
    require_db()
    st.title("Portfolio overview")
    st.caption("Sharp KPIs for the gold-layer transaction fact table.")
    currency_warning()
    st.markdown("---")

    kpis = fetch_df(
        """
        SELECT
            COUNT(*) AS total_transactions,
            ROUND(CAST(SUM(gross_amount) AS DOUBLE), 2) AS total_gross_amount,
            ROUND(CAST(SUM(fee) AS DOUBLE), 2) AS total_fees,
            ROUND(CAST(AVG(gross_amount) AS DOUBLE), 2) AS average_transaction_value
        FROM gold.fact_transactions
        """
    )

    row = kpis.iloc[0]
    top_currency = fetch_df(
        """
        SELECT currency, COUNT(*) AS transactions
        FROM gold.fact_transactions
        GROUP BY currency
        ORDER BY transactions DESC
        LIMIT 1
        """
    )
    top_currency_name = (
        top_currency.iloc[0]["currency"] if not top_currency.empty else "N/A"
    )
    top_currency_transactions = (
        top_currency.iloc[0]["transactions"] if not top_currency.empty else 0
    )

    top_type = fetch_df(
        """
        SELECT COALESCE(dtt.transaction_type_name, 'Unknown') AS transaction_type,
               ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_transaction_types dtt
            ON dtt.transaction_type_id = t.transaction_type_id
        GROUP BY COALESCE(dtt.transaction_type_name, 'Unknown')
        ORDER BY gross_amount DESC
        LIMIT 1
        """
    )
    top_type_name = (
        top_type.iloc[0]["transaction_type"] if not top_type.empty else "N/A"
    )
    top_type_volume = top_type.iloc[0]["gross_amount"] if not top_type.empty else 0

    cards = [
        ("Transactions", format_number(row["total_transactions"]), "Total activity"),
        ("Gross volume", money(row["total_gross_amount"]), "Portfolio value"),
        ("Average value", money(row["average_transaction_value"]), "Per transaction"),
        (
            "Top currency",
            top_currency_name,
            f"{format_number(top_currency_transactions)} txns",
        ),
        (
            "Top transaction type",
            top_type_name,
            money(top_type_volume),
        ),
    ]

    cols = st.columns(5)
    for col, (label, value, caption) in zip(cols, cards):
        with col:
            st.metric(label=label, value=value, delta=caption)

    volume_by_month = fetch_df(
        """
        SELECT
            DATE_TRUNC('month', transaction_date) AS month,
            COUNT(*) AS transaction_count,
            ROUND(CAST(SUM(gross_amount) AS DOUBLE), 2) AS gross_amount
        FROM gold.fact_transactions
        WHERE transaction_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY month
        """
    )

    st.subheader("Monthly gross volume")
    st.line_chart(
        volume_by_month.set_index("month")["gross_amount"],
        x=None,
        y=None,
        width="stretch",
    )
    st.caption(
        "Business question: Is the portfolio expanding in value, or are we seeing a few large transactions distort the trend?"
    )


if __name__ == "__main__":
    main()
