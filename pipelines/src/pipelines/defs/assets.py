import os
from pathlib import Path

import dagster as dg

from pipelines.logic.controllers.landing_zone_controller import LandingZoneController
from pipelines.logic.impl.connectors.http_api_connector import HTTPConnector
from pipelines.logic.impl.storage.fs import FSStorage

#
# DEFS AND CONFIGS -> this usually goes to config files and env variables
#

DOCKER_SOURCE = "http://financial_transactions_etl_json_server:3001"
LOCAL_SOURCE = "http://localhost:3001"
SOURCE = LOCAL_SOURCE
PROJECT_ROOT = Path(__file__).resolve().parents[4]

storage = FSStorage(root=str(Path(os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data")))))

api_feed_connector = HTTPConnector(url=f"{SOURCE}/API_FEED")
crm_export_connector = HTTPConnector(url=f"{SOURCE}/CRM_EXPORT")
legacy_system_connector = HTTPConnector(url=f"{SOURCE}/LEGACY_SYS")
manual_uploader_connector = HTTPConnector(url=f"{SOURCE}/MANUAL_UPLOAD")
partner_feed_connector = HTTPConnector(url=f"{SOURCE}/PARTNER_FEED")

landing_zone_controller = LandingZoneController(
    connectors=[
        api_feed_connector,
        crm_export_connector,
        legacy_system_connector,
        manual_uploader_connector,
        partner_feed_connector,
    ],
    sink=storage,
)


#
# Pipelines and assets
#


@dg.asset(pool="duckdb")
def landing_zone() -> dg.MaterializeResult:
    result = landing_zone_controller.fetch_data()
    return dg.MaterializeResult(
        asset_key=dg.AssetKey("landing_zone"),
        metadata={"landing_zone_fetched_data": result},
    )
