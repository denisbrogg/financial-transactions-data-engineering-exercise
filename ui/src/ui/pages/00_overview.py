import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.db import fetch_df, fmt_chf, fmt_pct, require_db


@st.cache_data(ttl=3600, show_spinner=False)
def load_date_bounds() -> tuple[str | None, str | None]:
    row = fetch_df(
        """
        SELECT
            MIN(transaction_date) AS min_date,
            MAX(transaction_date) AS max_date
        FROM gold.fact_transactions
        """
    ).iloc[0]
    return row["min_date"], row["max_date"]


@st.cache_data(ttl=3600, show_spinner=False)
def load_overview_data(
    date_from: str,
    date_to: str,
    selected_types: tuple[str, ...],
    status_filter: str,
) -> pd.DataFrame:
    query = """
        SELECT
            t.transaction_date,
            COALESCE(dtt.transaction_type_name, 'Unknown') AS transaction_type,
            COALESCE(dc.channel_name, 'Unknown') AS channel,
            COALESCE(dcl.client_name, 'Unknown') AS client_name,
            t.gross_amount,
            t.fee,
            COALESCE(t.is_flagged, FALSE) AS is_flagged
        FROM gold.fact_transactions t
        LEFT JOIN gold.dim_transaction_types dtt
            ON dtt.transaction_type_id = t.transaction_type_id
        LEFT JOIN gold.dim_channels dc
            ON dc.channel_id = t.channel_id
        LEFT JOIN gold.dim_clients dcl
            ON dcl.client_id = t.client_id
        WHERE t.transaction_date BETWEEN ? AND ?
    """
    df = fetch_df(query, (date_from, date_to))

    if selected_types:
        df = df[df["transaction_type"].isin(selected_types)]

    if status_filter == "Flagged":
        df = df[df["is_flagged"].fillna(False).astype(bool)]
    elif status_filter == "Clean":
        df = df[~df["is_flagged"].fillna(False).astype(bool)]

    return df.reset_index(drop=True)


def calculate_period_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_volume": 0.0,
            "fee_yield": 0.0,
            "flagged_rate": 0.0,
        }

    total_volume = float(df["gross_amount"].fillna(0).sum())
    fee_total = float(df["fee"].fillna(0).sum())
    flagged_rate = float(df["is_flagged"].fillna(False).mean() * 100.0)
    fee_yield = (fee_total / total_volume * 100.0) if total_volume else 0.0

    return {
        "total_volume": total_volume,
        "fee_yield": fee_yield,
        "flagged_rate": flagged_rate,
    }


def build_top_clients(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["client_name", "client_volume"])

    client_volume = (
        df.groupby("client_name", as_index=False)["gross_amount"]
        .sum()
        .rename(columns={"gross_amount": "client_volume"})
        .sort_values("client_volume", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    return client_volume


def build_channel_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "channel", "gross_amount"])

    channel_trend = (
        df.assign(
            month=pd.to_datetime(df["transaction_date"]).dt.to_period("M").astype(str)
        )
        .groupby(["month", "channel"], as_index=False)["gross_amount"]
        .sum()
        .rename(columns={"gross_amount": "gross_amount"})
    )
    return channel_trend.sort_values(["month", "channel"]).reset_index(drop=True)


def main():
    require_db()
    st.title("5 KPIs")
    st.caption("Portfolio overview built from the gold transaction fact table.")

    min_date, max_date = load_date_bounds()
    min_date = (
        pd.to_datetime(min_date).date() if min_date else pd.Timestamp.today().date()
    )
    max_date = (
        pd.to_datetime(max_date).date() if max_date else pd.Timestamp.today().date()
    )

    type_options = [
        row[0]
        for row in fetch_df(
            "SELECT transaction_type_name FROM gold.dim_transaction_types ORDER BY transaction_type_name"
        ).itertuples(index=False, name=None)
    ]

    st.sidebar.subheader("Filters")
    selected_range = st.sidebar.date_input(
        "Date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
    )
    if isinstance(selected_range, tuple):
        date_from, date_to = selected_range
    else:
        date_from = selected_range
        date_to = selected_range
    date_from = pd.to_datetime(date_from).date()
    date_to = pd.to_datetime(date_to).date()

    selected_types = st.sidebar.multiselect(
        "Asset class",
        options=type_options,
        default=type_options,
    )
    status_filter = st.sidebar.radio(
        "Status",
        ["All", "Flagged", "Clean"],
        horizontal=True,
    )

    current_df = load_overview_data(
        date_from.isoformat(),
        date_to.isoformat(),
        tuple(selected_types),
        status_filter,
    )

    if current_df.empty:
        st.info("No transactions match the selected filters.")
        return

    span_days = max((date_to - date_from).days + 1, 1)
    prior_end = date_from - timedelta(days=1)
    prior_start = prior_end - timedelta(days=span_days - 1)
    prior_df = load_overview_data(
        prior_start.isoformat(),
        prior_end.isoformat(),
        tuple(selected_types),
        status_filter,
    )

    current_metrics = calculate_period_metrics(current_df)
    previous_metrics = calculate_period_metrics(prior_df)

    total_delta = current_metrics["total_volume"] - previous_metrics["total_volume"]
    total_delta_pct = (
        (total_delta / previous_metrics["total_volume"]) * 100.0
        if previous_metrics["total_volume"]
        else 0.0
    )

    fee_delta = current_metrics["fee_yield"] - previous_metrics["fee_yield"]
    flag_delta = current_metrics["flagged_rate"] - previous_metrics["flagged_rate"]

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="Total volume (CHF)",
        value=fmt_chf(current_metrics["total_volume"], 0),
        delta=f"{total_delta_pct:+.1f}% vs prev. period",
        delta_color="normal",
    )
    st.caption(
        "This KPI shows the total completed value in the selected window so you can see whether the portfolio is growing or contracting."
    )

    col2.metric(
        label="Fee yield",
        value=fmt_pct(current_metrics["fee_yield"], 2),
        delta=f"{fee_delta:+.2f}pp vs prev. period",
        delta_color="normal",
    )
    st.caption(
        "This KPI tracks how much revenue the portfolio generates relative to transaction value, highlighting margin quality across the period."
    )

    col3.metric(
        label="Flagged rate",
        value=fmt_pct(current_metrics["flagged_rate"], 1),
        delta=f"{flag_delta:+.1f}pp vs prev. period",
        delta_color="inverse",
    )
    st.caption(
        "This KPI highlights operational risk by showing how much of the selected volume is flagged, which helps flag exceptions before they escalate."
    )

    st.markdown("---")

    top_clients = build_top_clients(current_df)
    if not top_clients.empty:
        top_clients_total = float(top_clients["client_volume"].sum())
        top_clients_share = (
            (top_clients_total / current_metrics["total_volume"]) * 100.0
            if current_metrics["total_volume"]
            else 0.0
        )
        st.subheader("Top clients")
        st.caption(
            f"Top 10 clients account for {top_clients_share:.1f}% of selected volume."
        )
        st.caption(
            "This chart shows concentration risk by highlighting which clients dominate the book and whether a small number of accounts drive most of the flow."
        )

        top_clients_sorted = top_clients.sort_values(
            "client_volume", ascending=True
        ).reset_index(drop=True)
        fig = px.bar(
            top_clients_sorted,
            x="client_volume",
            y="client_name",
            orientation="h",
            text="client_volume",
            title="Top 10 clients by volume",
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            margin={"l": 0, "r": 40, "t": 40, "b": 0},
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    channel_trend = build_channel_trend(current_df)
    if not channel_trend.empty:
        channel_mix = channel_trend.copy()
        channel_mix["transaction_month"] = pd.to_datetime(channel_mix["month"])
        channel_mix = channel_mix.sort_values(
            ["transaction_month", "channel"]
        ).reset_index(drop=True)

        monthly_totals = (
            channel_mix.groupby("transaction_month", as_index=False)["gross_amount"]
            .sum()
            .rename(columns={"gross_amount": "month_total"})
        )
        monthly_totals["cum_total_volume"] = monthly_totals["month_total"].cumsum()
        channel_mix = channel_mix.merge(
            monthly_totals[["transaction_month", "cum_total_volume"]],
            on="transaction_month",
            how="left",
        )

        channel_mix["cum_channel_volume"] = channel_mix.groupby("channel")[
            "gross_amount"
        ].cumsum()
        channel_mix["cum_share_pct"] = (
            channel_mix["cum_channel_volume"] / channel_mix["cum_total_volume"] * 100.0
        )

        st.subheader("Channel mix shift")
        st.caption(
            "This chart shows the cumulative share of total selected volume attributable to each channel, making it easy to see which channels are gaining long-term contribution over time."
        )

        fig = px.area(
            channel_mix,
            x="transaction_month",
            y="cum_share_pct",
            color="channel",
            groupnorm="percent",
            title="Cumulative channel contribution over time",
            labels={
                "transaction_month": "",
                "cum_share_pct": "Cumulative share of volume (%)",
                "channel": "Channel",
            },
        )
        fig.update_traces(
            hovertemplate="%{fullData.name}: %{y:.1f}% cumulative<extra></extra>"
        )
        fig.update_layout(
            yaxis={
                "ticksuffix": "%",
                "range": [0, 100],
                "title": "Cumulative share of volume",
            },
            xaxis_title=None,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": -0.25,
                "xanchor": "center",
                "x": 0.5,
                "title": None,
            },
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            height=400,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
