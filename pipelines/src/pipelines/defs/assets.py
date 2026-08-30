import os
from pathlib import Path

import dagster as dg
import duckdb

from pipelines.logic.controllers.bronze_controller import BronzeController
from pipelines.logic.controllers.gold_controller import GoldController
from pipelines.logic.controllers.landing_zone_controller import LandingZoneController
from pipelines.logic.controllers.silver_controller import SilverController
from pipelines.logic.impl.connectors.full_csv_connector import FullCSVConnector
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
from pipelines.logic.impl.ingestors.full_csv_ingestor import FullCSVIngestor
from pipelines.logic.impl.silver.cleaners.encoding import EncodingCleaner
from pipelines.logic.impl.silver.cleaners.flagged import FlaggedTransactionCleaner
from pipelines.logic.impl.silver.cleaners.numeric import NumericCleaner
from pipelines.logic.impl.silver.cleaners.spaces import SpacesCleaner
from pipelines.logic.impl.silver.cleaners.typos import CategoryTypoCleaner
from pipelines.logic.impl.silver.normalizers.category_normalizer import (
    CategoryNormalizer,
)
from pipelines.logic.impl.silver.normalizers.date_normalizer import DateNormalizer

#
# DEFS AND CONFIGS -> this usually goes to config files and env variables
#

data_root = Path(os.getenv("DATA_ROOT", "/data"))
data_source = f"{data_root}/sources/financial_transactions_raw.csv"

landing_zone_controller = LandingZoneController(
    source=str(data_source),
    sink=str(data_root / "landing_zone"),
    connectors=[
        FullCSVConnector(source_path=str(data_source)),
    ],
)

bronze_layer_controller = BronzeController(
    source=str(data_root / "landing_zone"),
    sink=str(data_root / "db" / "transactions.duckdb"),
    ingestors=[
        FullCSVIngestor(
            source=str(data_root / "landing_zone"),
        ),
    ],
)

silver_layer_controller = SilverController(
    source=str(data_root / "db" / "transactions.duckdb"),
    sink=str(data_root / "db" / "transactions.duckdb"),
    cleaners=[
        EncodingCleaner(),
        SpacesCleaner(),
        CategoryTypoCleaner(),
        NumericCleaner(),
        FlaggedTransactionCleaner(),
    ],
    standardizers=[CategoryNormalizer(), DateNormalizer()],
    deduplicators=[],
)

gold_layer_controller = GoldController(
    source=str(data_root / "db" / "transactions.duckdb"),
    sink=str(data_root / "db" / "transactions.duckdb"),
    loaders=[
        ClientDimensionLoader(),
        AdvisorDimensionLoader(),
        InstrumentDimensionLoader(),
        PortfolioDimensionLoader(),
        TransactionTypeDimensionLoader(),
        ClientPortfolioDimensionLoader(),
        ChannelDimensionLoader(),
        SourceSystemDimensionLoader(),
        TransactionFactLoader(),
    ],
)

#
# Pipelines and assets
#


@dg.asset(pool="duckdb")
def landing_zone(context) -> dg.MaterializeResult:
    landing_zone_controller.fetch_data()
    landing_files = list(Path(data_root / "landing_zone").glob("*.csv"))
    return dg.MaterializeResult(
        metadata={
            "source_path": str(data_root / "landing_zone"),
            "csv_files": len(landing_files),
        }
    )


@dg.asset(deps=["landing_zone"], pool="duckdb")
def bronze_layer(context) -> dg.MaterializeResult:
    bronze_layer_controller.ingest_data()
    with duckdb.connect(bronze_layer_controller.sink) as connection:
        bronze_row_count = connection.execute(
            'SELECT COUNT(*) FROM bronze."transaction"'
        ).fetchone()[0]

    return dg.MaterializeResult(
        metadata={
            "table": 'bronze."transaction"',
            "row_count": bronze_row_count,
            "sink": bronze_layer_controller.sink,
        }
    )


@dg.asset(deps=["bronze_layer"], pool="duckdb")
def silver_layer(context) -> dg.MaterializeResult:
    with duckdb.connect(silver_layer_controller.source) as connection:
        bronze_cursor = connection.execute('SELECT * FROM bronze."transaction"')
        columns = [column[0] for column in bronze_cursor.description]
        bronze_transactions = [
            dict(zip(columns, row)) for row in bronze_cursor.fetchall()
        ]

    curated_transactions = silver_layer_controller.curate_transactions(
        bronze_transactions
    )

    with duckdb.connect(silver_layer_controller.sink) as connection:
        silver_row_count = connection.execute(
            'SELECT COUNT(*) FROM silver."transaction"'
        ).fetchone()[0]

    return dg.MaterializeResult(
        metadata={
            "table": 'silver."transaction"',
            "row_count": silver_row_count,
            "curated_rows": len(curated_transactions),
            "sink": silver_layer_controller.sink,
        }
    )


@dg.asset(deps=["silver_layer"], pool="duckdb")
def gold_dim_clients(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(ClientDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_clients"], pool="duckdb")
def gold_dim_advisors(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(AdvisorDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_advisors"], pool="duckdb")
def gold_dim_instruments(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(InstrumentDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_instruments"], pool="duckdb")
def gold_dim_portfolios(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(PortfolioDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_portfolios"], pool="duckdb")
def gold_dim_transaction_types(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(TransactionTypeDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(
    deps=["gold_dim_clients", "gold_dim_portfolios"],
    pool="duckdb",
)
def gold_dim_client_portfolios(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(ClientPortfolioDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(
    deps=["gold_dim_transaction_types", "gold_dim_client_portfolios"],
    pool="duckdb",
)
def gold_dim_channels(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(ChannelDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_channels"], pool="duckdb")
def gold_dim_source_systems(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_dimension(SourceSystemDimensionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_dim_source_systems"], pool="duckdb")
def gold_flagged_transactions(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_fact(FlaggedTransactionLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})


@dg.asset(deps=["gold_flagged_transactions"], pool="duckdb")
def gold_fact_transactions(context) -> dg.MaterializeResult:
    gold_layer_controller.initialize_tables()
    row_count = gold_layer_controller.load_fact(TransactionFactLoader())
    return dg.MaterializeResult(metadata={"row_count": row_count})
