import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import currency_warning, fetch_df, require_db


def main():
    require_db()
    st.title("Analysis")
    currency_warning()
    st.caption("Monthly activity and portfolio composition by key breakdowns.")

    monthly_totals = fetch_df(
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

    st.subheader("Transaction volume")
    st.line_chart(
        monthly_totals.set_index("month")["gross_amount"],
        width="stretch",
    )
    st.caption(
        "Business question: Which months are carrying the highest portfolio value, and are there clear spikes or dips to investigate?"
    )

    st.subheader("Transaction count")
    st.line_chart(
        monthly_totals.set_index("month")["transaction_count"],
        width="stretch",
    )
    st.caption(
        "Business question: Is growth being driven by more transactions or by larger transaction sizes?"
    )

    breakdown_by = st.radio(
        "Breakdown by",
        ["Currency", "Transaction type"],
        horizontal=True,
    )

    if breakdown_by == "Currency":
        monthly_breakdown = fetch_df(
            """
            SELECT
                DATE_TRUNC('month', transaction_date) AS month,
                currency,
                COUNT(*) AS transaction_count,
                ROUND(CAST(SUM(gross_amount) AS DOUBLE), 2) AS gross_amount
            FROM gold.fact_transactions
            WHERE transaction_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', transaction_date), currency
            ORDER BY month, currency
            """
        )
        metric = "gross_amount"
        subtitle = "Transaction volume by currency"
        question = "Which currencies are driving the trend, and are we seeing genuine momentum or just more volume from one market?"
    else:
        monthly_breakdown = fetch_df(
            """
            SELECT
                DATE_TRUNC('month', t.transaction_date) AS month,
                COALESCE(dtt.transaction_type_name, 'Unknown') AS transaction_type,
                COUNT(*) AS transaction_count,
                ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount
            FROM gold.fact_transactions t
            LEFT JOIN gold.dim_transaction_types dtt
                ON dtt.transaction_type_id = t.transaction_type_id
            WHERE t.transaction_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', t.transaction_date), COALESCE(dtt.transaction_type_name, 'Unknown')
            ORDER BY month, transaction_type
            """
        )
        metric = "gross_amount"
        subtitle = "Transaction volume by transaction type"
        question = "Which transaction families are generating the most portfolio value over time?"

    pivot = monthly_breakdown.pivot_table(
        index="month",
        columns=("currency" if breakdown_by == "Currency" else "transaction_type"),
        values=metric,
        aggfunc="sum",
    ).fillna(0)

    st.subheader(subtitle)
    st.line_chart(pivot, width="stretch")
    st.caption(question)

    transaction_type_totals = fetch_df(
        """
        SELECT
            COALESCE(dtt.transaction_type_name, 'Unknown') AS transaction_type,
            ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_transaction_types dtt
            ON dtt.transaction_type_id = t.transaction_type_id
        GROUP BY COALESCE(dtt.transaction_type_name, 'Unknown')
        ORDER BY gross_amount DESC
        """
    )

    st.subheader("Overall volume by transaction type")
    fig = px.pie(
        transaction_type_totals,
        names="transaction_type",
        values="gross_amount",
        hole=0.55,
        title="Transaction type mix",
    )
    fig.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:,.0f} CHF (%{percent})",
    )
    fig.update_layout(
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Business question: How much of total portfolio volume is coming from each transaction type?"
    )


if __name__ == "__main__":
    main()
