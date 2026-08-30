import os
from pathlib import Path

import dagster as dg
import duckdb

DATABASE_PATH = str(
    Path(os.getenv("DATA_ROOT", "/data")) / "db" / "transactions.duckdb"
)


def _connect():
    return duckdb.connect(DATABASE_PATH, read_only=True)


@dg.asset_check(asset="gold_dim_clients", pool="duckdb")
def gold_dim_clients_no_null_pk() -> dg.AssetCheckResult:
    with _connect() as connection:
        null_count = connection.execute(
            "SELECT COUNT(*) FROM gold.dim_clients WHERE client_id IS NULL"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=null_count == 0, metadata={"null_pk_count": null_count}
    )


@dg.asset_check(asset="gold_dim_advisors", pool="duckdb")
def gold_dim_advisors_no_null_pk() -> dg.AssetCheckResult:
    with _connect() as connection:
        null_count = connection.execute(
            "SELECT COUNT(*) FROM gold.dim_advisors WHERE advisor_id IS NULL"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=null_count == 0, metadata={"null_pk_count": null_count}
    )


@dg.asset_check(asset="gold_dim_instruments", pool="duckdb")
def gold_dim_instruments_no_null_pk() -> dg.AssetCheckResult:
    with _connect() as connection:
        null_count = connection.execute(
            "SELECT COUNT(*) FROM gold.dim_instruments WHERE instrument_name IS NULL"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=null_count == 0, metadata={"null_pk_count": null_count}
    )


@dg.asset_check(asset="gold_dim_instruments", pool="duckdb")
def gold_dim_instruments_asset_class_values_known() -> dg.AssetCheckResult:
    with _connect() as connection:
        unexpected = connection.execute(
            """
            SELECT asset_class, COUNT(*) AS n
            FROM gold.dim_instruments
            WHERE asset_class IS NOT NULL
              AND TRIM(asset_class) <> ''
              AND asset_class NOT IN (
                  'Equity', 'Bond', 'ETF', 'Cash', 'Fund', 'Commodity',
                  'Real Estate', 'Crypto', 'Money Market'
              )
            GROUP BY asset_class
            ORDER BY asset_class
            """
        ).df()

    passed = len(unexpected) == 0
    metadata = {}
    if not passed:
        metadata["unexpected_values"] = dg.MetadataValue.md(
            unexpected.to_markdown(index=False)
        )
    return dg.AssetCheckResult(passed=passed, metadata=metadata)


@dg.asset_check(asset="gold_fact_transactions", pool="duckdb")
def gold_fact_no_null_pk() -> dg.AssetCheckResult:
    with _connect() as connection:
        null_count = connection.execute(
            "SELECT COUNT(*) FROM gold.fact_transactions WHERE transaction_id IS NULL"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=null_count == 0, metadata={"null_pk_count": null_count}
    )


@dg.asset_check(asset="gold_fact_transactions", pool="duckdb")
def gold_fact_no_negative_amounts() -> dg.AssetCheckResult:
    with _connect() as connection:
        bad_rows = connection.execute(
            "SELECT COUNT(*) FROM gold.fact_transactions WHERE gross_amount < 0 OR fee < 0"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=bad_rows == 0, metadata={"bad_amount_rows": bad_rows}
    )


@dg.asset_check(asset="gold_fact_transactions", pool="duckdb")
def gold_fact_fk_resolved() -> dg.AssetCheckResult:
    with _connect() as connection:
        orphan_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM gold.fact_transactions AS f
            LEFT JOIN gold.dim_clients AS dc ON dc.client_id = f.client_id
            LEFT JOIN gold.dim_advisors AS da ON da.advisor_id = f.advisor_id
            LEFT JOIN gold.dim_instruments AS di ON di.instrument_id = f.instrument_id
            LEFT JOIN gold.dim_portfolios AS dp ON dp.portfolio_id = f.portfolio_id
            LEFT JOIN gold.dim_transaction_types AS dtt ON dtt.transaction_type_id = f.transaction_type_id
            LEFT JOIN gold.dim_channels AS dc2 ON dc2.channel_id = f.channel_id
            LEFT JOIN gold.dim_source_systems AS dss ON dss.source_system_id = f.source_system_id
            WHERE dc.client_id IS NULL
               OR (f.advisor_id IS NOT NULL AND da.advisor_id IS NULL)
               OR (f.instrument_id IS NOT NULL AND di.instrument_id IS NULL)
               OR (f.portfolio_id IS NOT NULL AND dp.portfolio_id IS NULL)
               OR (f.transaction_type_id IS NOT NULL AND dtt.transaction_type_id IS NULL)
               OR dc2.channel_id IS NULL
               OR dss.source_system_id IS NULL
            """
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=orphan_rows == 0, metadata={"orphan_row_count": orphan_rows}
    )


@dg.asset_check(asset="gold_fact_transactions", pool="duckdb")
def gold_fact_transaction_date_range() -> dg.AssetCheckResult:
    with _connect() as connection:
        future_rows = connection.execute(
            "SELECT COUNT(*) FROM gold.fact_transactions WHERE transaction_date > CURRENT_DATE"
        ).fetchone()[0]
    return dg.AssetCheckResult(
        passed=future_rows == 0, metadata={"future_row_count": future_rows}
    )
