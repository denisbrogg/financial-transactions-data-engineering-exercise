import sys
from pathlib import Path

import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import fetch_df, require_db


def main():
    require_db()
    st.title("General customer behaviour and preferences")

    asset_rank = fetch_df(
        """
        SELECT
            COALESCE(i.instrument_name, 'Unknown') AS instrument_name,
            COUNT(*) AS trades,
            ROUND(CAST(SUM(t.gross_amount) AS DOUBLE), 2) AS gross_amount
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_instruments i ON i.instrument_id = t.instrument_id
        GROUP BY COALESCE(i.instrument_name, 'Unknown')
        ORDER BY trades DESC, gross_amount DESC
        LIMIT 10
        """
    )

    currency_rank = fetch_df(
        """
        SELECT currency, COUNT(*) AS transactions
        FROM gold.fact_transactions
        GROUP BY currency
        ORDER BY transactions DESC
        """
    )

    channel_rank = fetch_df(
        """
        SELECT
            COALESCE(c.channel_name, 'Unknown') AS channel_name,
            COUNT(*) AS transactions
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_channels c ON c.channel_id = t.channel_id
        GROUP BY COALESCE(c.channel_name, 'Unknown')
        ORDER BY transactions DESC
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Most traded assets")
        st.bar_chart(
            asset_rank.sort_values("trades", ascending=False).set_index(
                "instrument_name"
            )["trades"],
            horizontal=True,
            width="stretch",
        )
        st.caption(
            "Business question: Which instruments are customers engaging with most, and where should we focus product or advisory attention?"
        )

    with col2:
        st.subheader("Most used currencies")
        st.bar_chart(
            currency_rank.sort_values("transactions", ascending=False).set_index(
                "currency"
            )["transactions"],
            horizontal=True,
            width="stretch",
        )
        st.caption(
            "Business question: Which currencies dominate customer demand, and are we exposed to concentration risk?"
        )

    with col3:
        st.subheader("Ranked channels")
        st.bar_chart(
            channel_rank.sort_values("transactions", ascending=False).set_index(
                "channel_name"
            )["transactions"],
            horizontal=True,
            width="stretch",
        )
        st.caption(
            "Business question: Which channels are driving the most activity, and where should customer experience investment go?"
        )

    st.subheader("Underlying ranking tables")
    tabs = st.tabs(["Assets", "Currencies", "Channels"])
    tabs[0].dataframe(
        asset_rank,
        width="stretch",
        hide_index=True,
        column_config={
            "instrument_name": st.column_config.TextColumn("Instrument"),
            "trades": st.column_config.NumberColumn("Trades", format="%d"),
            "gross_amount": st.column_config.NumberColumn(
                "Gross amount", format="CHF %.2f"
            ),
        },
    )
    tabs[0].caption(
        "Business question: Which assets are genuinely winning customer preference across the portfolio?"
    )
    tabs[1].dataframe(currency_rank, width="stretch", hide_index=True)
    tabs[1].caption(
        "Business question: Are preferences clustered in a few currencies, or is the customer base diversified?"
    )
    tabs[2].dataframe(channel_rank, width="stretch", hide_index=True)
    tabs[2].caption(
        "Business question: Which channel mix is producing the strongest customer engagement and conversion?"
    )


if __name__ == "__main__":
    main()
