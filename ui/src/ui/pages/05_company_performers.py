import sys
from pathlib import Path

import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import fetch_df, require_db


def main():
    require_db()
    st.title("Company performers")

    advisor_metrics = fetch_df(
        """
        SELECT
            COALESCE(a.advisor_name, 'Unknown') AS advisor_name,
            COUNT(*) AS transactions,
            ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount,
            ROUND(CAST(SUM(t.fee) AS DOUBLE), 2) AS fees
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_advisors a ON a.advisor_id = t.advisor_id
        GROUP BY COALESCE(a.advisor_name, 'Unknown')
        ORDER BY transactions DESC, gross_amount DESC
        LIMIT 10
        """
    )

    advisor_by_fee = advisor_metrics.sort_values("fees", ascending=False).reset_index(
        drop=True
    )

    st.subheader("Most active advisors by transaction count")
    st.dataframe(
        advisor_metrics,
        width="stretch",
        hide_index=True,
        column_config={
            "advisor_name": st.column_config.TextColumn("Advisor"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "gross_amount": st.column_config.NumberColumn(
                "Gross amount", format="€%.2f"
            ),
            "fees": st.column_config.NumberColumn("Fees", format="€%.2f"),
        },
    )
    st.caption(
        "Business question: Which advisors are creating the most operational activity, and where is execution volume clustering?"
    )

    st.subheader("Best advisors by fee")
    st.dataframe(
        advisor_by_fee[["advisor_name", "transactions", "gross_amount", "fees"]],
        width="stretch",
        hide_index=True,
        column_config={
            "advisor_name": st.column_config.TextColumn("Advisor"),
            "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "gross_amount": st.column_config.NumberColumn(
                "Gross amount", format="€%.2f"
            ),
            "fees": st.column_config.NumberColumn("Fees", format="€%.2f"),
        },
    )
    st.caption(
        "Business question: Which advisors are generating the most revenue quality, and which are strong on activity but weaker on monetization?"
    )
    st.caption(
        "This section supports advisor ranking, productivity checks, and revenue quality analysis."
    )

    st.caption(
        "Next step: add adviser performance vs. client mix and profitability efficiency."
    )


if __name__ == "__main__":
    main()
