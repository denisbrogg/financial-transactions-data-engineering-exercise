import os
from pathlib import Path

import dagster as dg
import duckdb

from pipelines.logic.controllers.bronze_controller import BronzeController
from pipelines.logic.controllers.landing_zone_controller import LandingZoneController
from pipelines.logic.controllers.silver_controller import SilverController
from pipelines.logic.impl.connectors.full_csv_connector import FullCSVConnector
from pipelines.logic.impl.ingestors.full_csv_ingestor import FullCSVIngestor
from pipelines.logic.impl.silver.cleaners.encoding import EncodingCleaner
from pipelines.logic.impl.silver.cleaners.spaces import SpacesCleaner
from pipelines.logic.impl.silver.cleaners.typos import CategoryTypoCleaner
from pipelines.logic.impl.silver.normalizers.category_normalizer import (
    CategoryNormalizer,
)

#
# DEFS AND CONFIGS -> this usually goes to config files and env variables
#

data_root = Path(os.getenv("DATA_ROOT", "/data"))
data_source = f"{data_root}/sources/financial_transactions_raw.csv"

landing_zone_controller = LandingZoneController(
    sink=str(data_root / "landing_zone"),
    connectors=[
        FullCSVConnector(source_path=str(data_source)),
    ],
)

bronze_layer_controller = BronzeController(
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
    cleaners=[EncodingCleaner(), SpacesCleaner(), CategoryTypoCleaner()],
    standardizers=[CategoryNormalizer()],
    deduplicators=[],
)

#
# Pipelines and assets
#


@dg.asset
def landing_zone(context) -> None:
    return landing_zone_controller.fetch_data()


@dg.asset(deps=["landing_zone"])
def bronze_layer(context) -> None:
    return bronze_layer_controller.ingest_data()


@dg.asset(deps=["bronze_layer"])
def silver_layer(context) -> list[dict]:
    with duckdb.connect(silver_layer_controller.source) as connection:
        bronze_cursor = connection.execute('SELECT * FROM bronze."transaction"')
        columns = [column[0] for column in bronze_cursor.description]
        bronze_transactions = [
            dict(zip(columns, row)) for row in bronze_cursor.fetchall()
        ]

    curated_transactions = silver_layer_controller.curate_transactions(
        bronze_transactions
    )

    return curated_transactions
