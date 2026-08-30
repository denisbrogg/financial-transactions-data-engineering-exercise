from unittest.mock import patch

import duckdb
from pipelines.defs import assets, checks
from pipelines.defs.checks import gold_dim_instruments_asset_class_values_known
from pipelines.logic.controllers.gold_controller import GoldController
from pipelines.logic.impl.gold.loaders import (
    AdvisorDimensionLoader,
    ChannelDimensionLoader,
    ClientDimensionLoader,
    ClientPortfolioDimensionLoader,
    FlaggedTransactionLoader,
    InstrumentDimensionLoader,
    PortfolioDimensionLoader,
    SourceSystemDimensionLoader,
    TransactionFactLoader,
    TransactionTypeDimensionLoader,
)
from pipelines.logic.impl.silver.normalizers.category_normalizer import (
    CategoryNormalizer,
)


def test_gold_schema_initializes_expected_tables(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    controller.initialize_tables()

    with duckdb.connect(str(database_path)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'gold'"
            ).fetchall()
        }

    assert {
        "dim_clients",
        "dim_advisors",
        "dim_instruments",
        "dim_portfolios",
        "dim_transaction_types",
        "dim_client_portfolios",
        "dim_channels",
        "dim_source_systems",
        "fact_transactions",
        "flagged_transactions",
    }.issubset(tables)


def test_gold_fact_excludes_flagged_transactions_and_keeps_them_separate(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS silver."transaction" (
                transaction_id VARCHAR,
                source_system VARCHAR,
                client_id VARCHAR,
                client_name VARCHAR,
                client_country VARCHAR,
                risk_profile VARCHAR,
                advisor_id VARCHAR,
                advisor_name VARCHAR,
                channel VARCHAR,
                portfolio_id VARCHAR,
                transaction_date DATE,
                asset_class VARCHAR,
                instrument_name VARCHAR,
                transaction_type VARCHAR,
                quantity VARCHAR,
                price_per_unit VARCHAR,
                currency VARCHAR,
                gross_amount VARCHAR,
                fee VARCHAR,
                status VARCHAR,
                notes VARCHAR,
                is_flagged BOOLEAN
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver."transaction" (
                transaction_id, source_system, client_id, client_name, client_country,
                risk_profile, advisor_id, advisor_name, channel, portfolio_id,
                transaction_date, asset_class, instrument_name, transaction_type,
                quantity, price_per_unit, currency, gross_amount, fee, status, notes, is_flagged
            ) VALUES
                ('t-normal', 'Bank', 'c1', 'Alice', 'CH', 'Balanced', 'a1', 'Advisor One', 'Online', 'p1', DATE '2024-01-01', 'Equity', 'AAPL', 'BUY', '10', '100', 'USD', '50000', '5', 'ok', 'normal trade', false),
                ('t-outlier', 'Bank', 'c2', 'Bob', 'US', 'Growth', 'a2', 'Advisor Two', 'Online', 'p2', DATE '2024-01-02', 'Equity', 'MSFT', 'BUY', '1', '100000001', 'USD', '100000001', '150', 'flagged', 'suspicious', true)
            """
        )

    controller.initialize_tables()
    controller.load_dimension(InstrumentDimensionLoader())
    controller.load_dimension(PortfolioDimensionLoader())
    controller.load_dimension(TransactionTypeDimensionLoader())
    controller.load_dimension(ClientDimensionLoader())
    controller.load_dimension(AdvisorDimensionLoader())
    controller.load_dimension(ClientPortfolioDimensionLoader())
    controller.load_dimension(ChannelDimensionLoader())
    controller.load_dimension(SourceSystemDimensionLoader())
    controller.load_fact(FlaggedTransactionLoader())
    controller.load_fact(TransactionFactLoader())

    with duckdb.connect(str(database_path)) as connection:
        fact_count = connection.execute(
            "SELECT COUNT(*) FROM gold.fact_transactions"
        ).fetchone()[0]
        flagged_count = connection.execute(
            "SELECT COUNT(*) FROM gold.flagged_transactions"
        ).fetchone()[0]
        fact_ids = connection.execute(
            "SELECT transaction_id FROM gold.fact_transactions ORDER BY transaction_id"
        ).fetchall()
        flagged_ids = connection.execute(
            "SELECT transaction_id FROM gold.flagged_transactions ORDER BY transaction_id"
        ).fetchall()

    assert fact_count == 1
    assert fact_ids == [("t-normal",)]
    assert flagged_count == 1
    assert flagged_ids == [("t-outlier",)]


def test_client_portfolio_asset_waits_for_client_dimension():
    dependency_keys = assets.gold_dim_client_portfolios.dependency_keys

    assert "gold_dim_clients" in {key.to_user_string() for key in dependency_keys}


def test_gold_schema_initialization_preserves_loaded_dimensions(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    controller.initialize_tables()
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            "INSERT INTO gold.dim_clients VALUES ('C00147', 'Existing Client', NULL, NULL)"
        )

    controller.initialize_tables()

    with duckdb.connect(str(database_path), read_only=True) as connection:
        client_count = connection.execute(
            "SELECT COUNT(*) FROM gold.dim_clients WHERE client_id = 'C00147'"
        ).fetchone()[0]

    assert client_count == 1


def test_gold_fact_uses_dimension_ids_and_keeps_notes(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS silver."transaction" (
                transaction_id VARCHAR,
                source_system VARCHAR,
                client_id VARCHAR,
                client_name VARCHAR,
                client_country VARCHAR,
                risk_profile VARCHAR,
                advisor_id VARCHAR,
                advisor_name VARCHAR,
                channel VARCHAR,
                portfolio_id VARCHAR,
                transaction_date DATE,
                asset_class VARCHAR,
                instrument_name VARCHAR,
                transaction_type VARCHAR,
                quantity VARCHAR,
                price_per_unit VARCHAR,
                currency VARCHAR,
                gross_amount VARCHAR,
                fee VARCHAR,
                status VARCHAR,
                notes VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver."transaction" (
                transaction_id, source_system, client_id, client_name, client_country,
                risk_profile, advisor_id, advisor_name, channel, portfolio_id,
                transaction_date, asset_class, instrument_name, transaction_type,
                quantity, price_per_unit, currency, gross_amount, fee, status, notes
            ) VALUES
                ('t1', 'Bank', 'c1', 'Alice', 'CH', 'Balanced', 'a1', 'Advisor One', 'Online', 'p1', DATE '2024-01-01', 'Equity', 'AAPL', 'BUY', '10', '100', 'USD', '1000', '5', 'ok', 'Add to watchlist')
            """
        )

    controller.initialize_tables()
    controller.load_dimension(InstrumentDimensionLoader())
    controller.load_dimension(PortfolioDimensionLoader())
    controller.load_dimension(TransactionTypeDimensionLoader())
    controller.load_dimension(ClientDimensionLoader())
    controller.load_dimension(AdvisorDimensionLoader())
    controller.load_dimension(ClientPortfolioDimensionLoader())
    controller.load_dimension(ChannelDimensionLoader())
    controller.load_dimension(SourceSystemDimensionLoader())
    controller.load_fact(TransactionFactLoader())

    with duckdb.connect(str(database_path)) as connection:
        fact_columns = [
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = 'gold' AND table_name = 'fact_transactions' ORDER BY ordinal_position"
            ).fetchall()
        ]
        fact_row = connection.execute(
            "SELECT transaction_id, instrument_id, transaction_type_id, notes FROM gold.fact_transactions WHERE transaction_id = 't1'"
        ).fetchone()

    assert "instrument_id" in fact_columns
    assert "transaction_type_id" in fact_columns
    assert "notes" in fact_columns
    assert fact_row is not None
    assert fact_row[1] == "AAPL"
    assert fact_row[2] == "BUY"
    assert fact_row[3] == "Add to watchlist"


def test_gold_instrument_dimension_keeps_null_asset_class(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS silver."transaction" (
                instrument_name VARCHAR,
                asset_class VARCHAR,
                transaction_id VARCHAR,
                client_id VARCHAR,
                advisor_id VARCHAR,
                portfolio_id VARCHAR,
                channel VARCHAR,
                source_system VARCHAR,
                transaction_date DATE,
                transaction_type VARCHAR,
                quantity DOUBLE,
                price_per_unit DOUBLE,
                currency VARCHAR,
                gross_amount DECIMAL(18, 2),
                fee DECIMAL(18, 2),
                net_amount DECIMAL(18, 2)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver."transaction" (
                instrument_name, asset_class, transaction_id, client_id, advisor_id,
                portfolio_id, channel, source_system, transaction_date, transaction_type,
                quantity, price_per_unit, currency, gross_amount, fee, net_amount
            ) VALUES
                ('isin-1', NULL, 't1', 'c1', NULL, 'p1', 'Online', 'Bank', DATE '2024-01-01', 'BUY', 10, 100, 'USD', 1000, 10, 990),
                ('isin-2', 'Equity', 't2', 'c1', NULL, 'p1', 'Online', 'Bank', DATE '2024-01-02', 'BUY', 5, 200, 'USD', 1000, 10, 990)
            """
        )

    controller.initialize_tables()
    row_count = controller.load_dimension(InstrumentDimensionLoader())

    assert row_count == 2
    with duckdb.connect(str(database_path)) as connection:
        rows = connection.execute(
            "SELECT instrument_name, asset_class FROM gold.dim_instruments ORDER BY instrument_name"
        ).fetchall()

    assert rows == [("isin-1", None), ("isin-2", "Equity")]


def test_gold_instrument_asset_class_check_allows_empty_values(tmp_path):
    database_path = tmp_path / "transactions.duckdb"

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS gold.dim_instruments (
                instrument_name VARCHAR PRIMARY KEY,
                asset_class VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.dim_instruments (instrument_name, asset_class)
            VALUES
                ('isin-empty', ''),
                ('isin-equity', 'Equity'),
                ('isin-null', NULL)
            """
        )

    result = gold_dim_instruments_asset_class_values_known()

    assert result.passed is True


def test_gold_asset_check_uses_read_only_connection(tmp_path, monkeypatch):
    database_path = tmp_path / "transactions.duckdb"
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA gold")
        connection.execute(
            "CREATE TABLE gold.dim_clients (client_id VARCHAR, client_name VARCHAR)"
        )
    monkeypatch.setattr(checks, "DATABASE_PATH", str(database_path))

    with patch("pipelines.defs.checks.duckdb.connect", wraps=duckdb.connect) as connect:
        result = checks.gold_dim_clients_no_null_pk()

    assert result.passed is True
    connect.assert_called_once_with(str(database_path), read_only=True)


def test_category_normalizer_sets_unknown_asset_class_to_none():
    normalizer = CategoryNormalizer()
    standardized = {}

    normalizer.standardize_data({"asset_class": "Unknown Category"}, standardized)
    assert standardized["asset_class"] is None

    standardized = {}
    normalizer.standardize_data({"asset_class": "  "}, standardized)
    assert standardized["asset_class"] is None


def test_gold_instrument_dimension_sanitizes_unknown_fact_asset_classes(tmp_path):
    database_path = tmp_path / "transactions.duckdb"
    controller = GoldController(database_path=str(database_path))

    with duckdb.connect(str(database_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS silver."transaction" (
                instrument_name VARCHAR,
                asset_class VARCHAR,
                transaction_id VARCHAR,
                client_id VARCHAR,
                advisor_id VARCHAR,
                portfolio_id VARCHAR,
                channel VARCHAR,
                source_system VARCHAR,
                transaction_date DATE,
                transaction_type VARCHAR,
                quantity DOUBLE,
                price_per_unit DOUBLE,
                currency VARCHAR,
                gross_amount DECIMAL(18, 2),
                fee DECIMAL(18, 2),
                net_amount DECIMAL(18, 2)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver."transaction" (
                instrument_name, asset_class, transaction_id, client_id, advisor_id,
                portfolio_id, channel, source_system, transaction_date, transaction_type,
                quantity, price_per_unit, currency, gross_amount, fee, net_amount
            ) VALUES
                ('isin-unknown', 'Unknown Category', 't1', 'c1', NULL, 'p1', 'Online', 'Bank', DATE '2024-01-01', 'BUY', 10, 100, 'USD', 1000, 10, 990),
                ('isin-known', 'Equity', 't2', 'c1', NULL, 'p1', 'Online', 'Bank', DATE '2024-01-02', 'BUY', 5, 200, 'USD', 1000, 10, 990)
            """
        )

    controller.initialize_tables()
    row_count = controller.load_dimension(InstrumentDimensionLoader())

    assert row_count == 2
    with duckdb.connect(str(database_path)) as connection:
        rows = connection.execute(
            "SELECT instrument_name, asset_class FROM gold.dim_instruments ORDER BY instrument_name"
        ).fetchall()

    assert rows == [("isin-known", "Equity"), ("isin-unknown", None)]
