from __future__ import annotations

from pipelines.logic.abstractions.gold.table_loader import GoldTableLoader


def _has_column(
    connection, schema_name: str, table_name: str, column_name: str
) -> bool:
    row = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ? AND column_name = ?
        """,
        [schema_name, table_name, column_name],
    ).fetchone()
    return bool(row and row[0] > 0)


class ClientDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_clients (
                client_id, client_name, client_country, risk_profile
            )
            SELECT DISTINCT client_id, client_name, client_country, risk_profile
            FROM silver."transaction"
            WHERE client_id IS NOT NULL AND client_name IS NOT NULL
            """
        )
        return connection.execute("SELECT COUNT(*) FROM gold.dim_clients").fetchone()[0]


class AdvisorDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_advisors (advisor_id, advisor_name)
            SELECT DISTINCT advisor_id, advisor_name
            FROM silver."transaction"
            WHERE advisor_id IS NOT NULL AND advisor_name IS NOT NULL
            """
        )
        return connection.execute("SELECT COUNT(*) FROM gold.dim_advisors").fetchone()[
            0
        ]


class InstrumentDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_instruments (instrument_id, instrument_name, asset_class)
            SELECT DISTINCT
                instrument_name AS instrument_id,
                instrument_name,
                CASE
                    WHEN asset_class IS NULL OR TRIM(asset_class) = '' THEN NULL
                    WHEN asset_class IN (
                        'Equity', 'Bond', 'ETF', 'Cash', 'Fund', 'Commodity',
                        'Real Estate', 'Crypto', 'Money Market'
                    ) THEN asset_class
                    ELSE NULL
                END AS asset_class
            FROM silver."transaction"
            WHERE instrument_name IS NOT NULL
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.dim_instruments"
        ).fetchone()[0]


class PortfolioDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_portfolios (portfolio_id)
            SELECT DISTINCT portfolio_id
            FROM silver."transaction"
            WHERE portfolio_id IS NOT NULL
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.dim_portfolios"
        ).fetchone()[0]


class TransactionTypeDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_transaction_types (transaction_type_id, transaction_type_name)
            SELECT DISTINCT
                transaction_type AS transaction_type_id,
                transaction_type
            FROM silver."transaction"
            WHERE transaction_type IS NOT NULL
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.dim_transaction_types"
        ).fetchone()[0]


class ClientPortfolioDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_client_portfolios (client_id, portfolio_id)
            SELECT DISTINCT client_id, portfolio_id
            FROM silver."transaction"
            WHERE client_id IS NOT NULL AND portfolio_id IS NOT NULL
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.dim_client_portfolios"
        ).fetchone()[0]


class ChannelDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_channels (channel_id, channel_name)
            SELECT
                CAST(row_number() OVER (ORDER BY channel_name) AS INTEGER) +
                    COALESCE((SELECT MAX(channel_id) FROM gold.dim_channels), 0),
                channel_name
            FROM (
                SELECT DISTINCT channel AS channel_name
                FROM silver."transaction"
                WHERE channel IS NOT NULL
            ) AS distinct_channels
            """
        )
        return connection.execute("SELECT COUNT(*) FROM gold.dim_channels").fetchone()[
            0
        ]


class SourceSystemDimensionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO gold.dim_source_systems (
                source_system_id, source_system_name
            )
            SELECT
                CAST(row_number() OVER (ORDER BY source_system_name) AS INTEGER) +
                    COALESCE((SELECT MAX(source_system_id) FROM gold.dim_source_systems), 0),
                source_system_name
            FROM (
                SELECT DISTINCT source_system AS source_system_name
                FROM silver."transaction"
                WHERE source_system IS NOT NULL
            ) AS distinct_source_systems
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.dim_source_systems"
        ).fetchone()[0]


class FlaggedTransactionLoader(GoldTableLoader):
    def load(self, connection) -> int:
        flagged_predicate = (
            "COALESCE(st.is_flagged, FALSE)"
            if _has_column(connection, "silver", "transaction", "is_flagged")
            else "FALSE"
        )

        connection.execute(
            f"""
            INSERT OR IGNORE INTO gold.flagged_transactions (
                transaction_id, client_id, advisor_id, instrument_id, portfolio_id,
                channel_id, source_system_id, transaction_date, transaction_type_id,
                quantity, price_per_unit, currency, gross_amount, fee, net_amount,
                transaction_year, transaction_month, transaction_quarter, notes, is_flagged,
                flagged_reason
            )
            WITH parsed_transactions AS (
                SELECT
                    st.*,
                    CASE
                        WHEN instr(st.quantity, ',') > 0 AND instr(st.quantity, '.') > 0
                            AND instr(st.quantity, ',') > instr(st.quantity, '.')
                            THEN REPLACE(REPLACE(st.quantity, '.', ''), ',', '.')
                        WHEN instr(st.quantity, ',') > 0 AND instr(st.quantity, '.') = 0
                            THEN REPLACE(st.quantity, ',', '.')
                        ELSE REPLACE(st.quantity, ',', '')
                    END AS parsed_quantity,
                    CASE
                        WHEN instr(st.price_per_unit, ',') > 0 AND instr(st.price_per_unit, '.') > 0
                            AND instr(st.price_per_unit, ',') > instr(st.price_per_unit, '.')
                            THEN REPLACE(REPLACE(st.price_per_unit, '.', ''), ',', '.')
                        WHEN instr(st.price_per_unit, ',') > 0 AND instr(st.price_per_unit, '.') = 0
                            THEN REPLACE(st.price_per_unit, ',', '.')
                        ELSE REPLACE(st.price_per_unit, ',', '')
                    END AS parsed_price_per_unit,
                    CASE
                        WHEN instr(st.gross_amount, ',') > 0 AND instr(st.gross_amount, '.') > 0
                            AND instr(st.gross_amount, ',') > instr(st.gross_amount, '.')
                            THEN REPLACE(REPLACE(st.gross_amount, '.', ''), ',', '.')
                        WHEN instr(st.gross_amount, ',') > 0 AND instr(st.gross_amount, '.') = 0
                            THEN REPLACE(st.gross_amount, ',', '.')
                        ELSE REPLACE(st.gross_amount, ',', '')
                    END AS parsed_gross_amount,
                    CASE
                        WHEN instr(st.fee, ',') > 0 AND instr(st.fee, '.') > 0
                            AND instr(st.fee, ',') > instr(st.fee, '.')
                            THEN REPLACE(REPLACE(st.fee, '.', ''), ',', '.')
                        WHEN instr(st.fee, ',') > 0 AND instr(st.fee, '.') = 0
                            THEN REPLACE(st.fee, ',', '.')
                        ELSE REPLACE(st.fee, ',', '')
                    END AS parsed_fee,
                    COALESCE(
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%Y-%m-%d'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d/%m/%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%m/%d/%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d.%m.%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d-%m-%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d-%b-%Y')
                    ) AS parsed_transaction_date
                FROM silver."transaction" AS st
            )
            SELECT
                st.transaction_id,
                CASE WHEN dc_client.client_id IS NOT NULL THEN st.client_id END,
                st.advisor_id,
                CASE WHEN dc_instrument.instrument_id IS NOT NULL THEN dc_instrument.instrument_id END,
                st.portfolio_id,
                dc.channel_id,
                dss.source_system_id,
                CAST(st.parsed_transaction_date AS DATE),
                CASE WHEN dtt.transaction_type_id IS NOT NULL THEN dtt.transaction_type_id END,
                TRY_CAST(st.parsed_quantity AS DOUBLE),
                TRY_CAST(st.parsed_price_per_unit AS DOUBLE),
                UPPER(COALESCE(st.currency, 'USD')),
                TRY_CAST(st.parsed_gross_amount AS DECIMAL(18, 2)),
                COALESCE(TRY_CAST(st.parsed_fee AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2))),
                COALESCE(TRY_CAST(st.parsed_gross_amount AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2)))
                    - COALESCE(TRY_CAST(st.parsed_fee AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2))),
                EXTRACT(YEAR FROM st.parsed_transaction_date),
                EXTRACT(MONTH FROM st.parsed_transaction_date),
                (EXTRACT(MONTH FROM st.parsed_transaction_date) - 1) / 3 + 1,
                st.notes,
                TRUE,
                CASE
                    WHEN TRY_CAST(st.parsed_gross_amount AS DOUBLE) > 100000000 THEN 'gross_amount_exceeds_100m'
                    WHEN COALESCE(st.status, '') ILIKE '%flagged%' THEN 'status_flagged'
                    WHEN COALESCE(st.notes, '') <> '' THEN 'manual_review'
                    ELSE 'manual_review'
                END
            FROM parsed_transactions AS st
            LEFT JOIN gold.dim_clients AS dc_client ON dc_client.client_id = st.client_id
            LEFT JOIN gold.dim_instruments AS dc_instrument ON dc_instrument.instrument_name = st.instrument_name
            LEFT JOIN gold.dim_transaction_types AS dtt ON dtt.transaction_type_name = st.transaction_type
            LEFT JOIN gold.dim_channels AS dc ON dc.channel_name = st.channel
            LEFT JOIN gold.dim_source_systems AS dss ON dss.source_system_name = st.source_system
            WHERE st.transaction_id IS NOT NULL
              AND ({flagged_predicate} = TRUE OR TRY_CAST(st.gross_amount AS DOUBLE) > 100000000)
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.flagged_transactions"
        ).fetchone()[0]


class TransactionFactLoader(GoldTableLoader):
    def load(self, connection) -> int:
        flagged_predicate = (
            "COALESCE(st.is_flagged, FALSE)"
            if _has_column(connection, "silver", "transaction", "is_flagged")
            else "FALSE"
        )

        connection.execute(
            f"""
            INSERT OR IGNORE INTO gold.fact_transactions (
                transaction_id, client_id, advisor_id, instrument_id, portfolio_id,
                channel_id, source_system_id, transaction_date, transaction_type_id,
                quantity, price_per_unit, currency, gross_amount, fee, net_amount,
                transaction_year, transaction_month, transaction_quarter, notes, is_flagged
            )
            WITH parsed_transactions AS (
                SELECT
                    st.*,
                    CASE
                        WHEN instr(st.quantity, ',') > 0 AND instr(st.quantity, '.') > 0
                            AND instr(st.quantity, ',') > instr(st.quantity, '.')
                            THEN REPLACE(REPLACE(st.quantity, '.', ''), ',', '.')
                        WHEN instr(st.quantity, ',') > 0 AND instr(st.quantity, '.') = 0
                            THEN REPLACE(st.quantity, ',', '.')
                        ELSE REPLACE(st.quantity, ',', '')
                    END AS parsed_quantity,
                    CASE
                        WHEN instr(st.price_per_unit, ',') > 0 AND instr(st.price_per_unit, '.') > 0
                            AND instr(st.price_per_unit, ',') > instr(st.price_per_unit, '.')
                            THEN REPLACE(REPLACE(st.price_per_unit, '.', ''), ',', '.')
                        WHEN instr(st.price_per_unit, ',') > 0 AND instr(st.price_per_unit, '.') = 0
                            THEN REPLACE(st.price_per_unit, ',', '.')
                        ELSE REPLACE(st.price_per_unit, ',', '')
                    END AS parsed_price_per_unit,
                    CASE
                        WHEN instr(st.gross_amount, ',') > 0 AND instr(st.gross_amount, '.') > 0
                            AND instr(st.gross_amount, ',') > instr(st.gross_amount, '.')
                            THEN REPLACE(REPLACE(st.gross_amount, '.', ''), ',', '.')
                        WHEN instr(st.gross_amount, ',') > 0 AND instr(st.gross_amount, '.') = 0
                            THEN REPLACE(st.gross_amount, ',', '.')
                        ELSE REPLACE(st.gross_amount, ',', '')
                    END AS parsed_gross_amount,
                    CASE
                        WHEN instr(st.fee, ',') > 0 AND instr(st.fee, '.') > 0
                            AND instr(st.fee, ',') > instr(st.fee, '.')
                            THEN REPLACE(REPLACE(st.fee, '.', ''), ',', '.')
                        WHEN instr(st.fee, ',') > 0 AND instr(st.fee, '.') = 0
                            THEN REPLACE(st.fee, ',', '.')
                        ELSE REPLACE(st.fee, ',', '')
                    END AS parsed_fee,
                    COALESCE(
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%Y-%m-%d'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d/%m/%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%m/%d/%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d.%m.%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d-%m-%Y'),
                        TRY_STRPTIME(CAST(st.transaction_date AS VARCHAR), '%d-%b-%Y')
                    ) AS parsed_transaction_date
                FROM silver."transaction" AS st
            )
            SELECT
                st.transaction_id,
                CASE WHEN dc_client.client_id IS NOT NULL THEN st.client_id END,
                st.advisor_id,
                CASE WHEN dc_instrument.instrument_id IS NOT NULL THEN dc_instrument.instrument_id END,
                st.portfolio_id,
                dc.channel_id,
                dss.source_system_id,
                CAST(st.parsed_transaction_date AS DATE),
                CASE WHEN dtt.transaction_type_id IS NOT NULL THEN dtt.transaction_type_id END,
                TRY_CAST(st.parsed_quantity AS DOUBLE),
                TRY_CAST(st.parsed_price_per_unit AS DOUBLE),
                UPPER(COALESCE(st.currency, 'USD')),
                TRY_CAST(st.parsed_gross_amount AS DECIMAL(18, 2)),
                COALESCE(TRY_CAST(st.parsed_fee AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2))),
                COALESCE(TRY_CAST(st.parsed_gross_amount AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2)))
                    - COALESCE(TRY_CAST(st.parsed_fee AS DECIMAL(18, 2)), CAST(0 AS DECIMAL(18, 2))),
                EXTRACT(YEAR FROM st.parsed_transaction_date),
                EXTRACT(MONTH FROM st.parsed_transaction_date),
                (EXTRACT(MONTH FROM st.parsed_transaction_date) - 1) / 3 + 1,
                st.notes,
                CASE
                    WHEN {flagged_predicate} = TRUE THEN TRUE
                    WHEN COALESCE(st.status, '') ILIKE '%flagged%' THEN TRUE
                    WHEN COALESCE(st.notes, '') <> '' THEN TRUE
                    ELSE FALSE
                END
            FROM parsed_transactions AS st
            LEFT JOIN gold.dim_clients AS dc_client ON dc_client.client_id = st.client_id
            LEFT JOIN gold.dim_instruments AS dc_instrument ON dc_instrument.instrument_name = st.instrument_name
            LEFT JOIN gold.dim_transaction_types AS dtt ON dtt.transaction_type_name = st.transaction_type
            LEFT JOIN gold.dim_channels AS dc ON dc.channel_name = st.channel
            LEFT JOIN gold.dim_source_systems AS dss ON dss.source_system_name = st.source_system
            WHERE st.transaction_id IS NOT NULL
              AND {flagged_predicate} = FALSE
            """
        )
        return connection.execute(
            "SELECT COUNT(*) FROM gold.fact_transactions"
        ).fetchone()[0]
