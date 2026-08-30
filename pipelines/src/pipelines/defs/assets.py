import os
from pathlib import Path

import dagster as dg

from pipelines.lib.controllers.landing_zone_controller import LandingZoneController
from pipelines.lib.impl.connectors.full_csv_connector import FullCSVConnector

#
# DEFS AND CONFIGS -> this usually goes to config files and env variables
#

data_root = Path(os.getenv("DATA_ROOT", "/data"))
data_source = f"{data_root}/sources/financial_transactions_raw.csv"

landing_zone_controller = LandingZoneController(
    landing_zone=str(data_root / "landing_zone"),
    connectors=[
        FullCSVConnector(source_path=str(data_source)),
    ],
)

#
# Pipelines and assets
#


@dg.asset
def landing_zone(context) -> None:
    return landing_zone_controller.fetch_data()
