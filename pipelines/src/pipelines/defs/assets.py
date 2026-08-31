from pathlib import Path

import dagster as dg

from pipelines.logic.controllers.landing_zone_controller import LandingZoneController
from pipelines.logic.impl.connectors.http_api_connector import HTTPConnector
from pipelines.logic.impl.storage.fs import FSStorage

#
# DEFS AND CONFIGS -> this usually goes to config files and env variables
#

storage = FSStorage(root=str(Path(__file__).resolve().parent.parent / "data"))

api_feed_connector = HTTPConnector(
    url="http://financial_transactions_etl_json_server:3001/API_FEED"
)
crm_export_connector = HTTPConnector(
    url="http://financial_transactions_etl_json_server:3001/CRM_EXPORT"
)
legacy_system_connector = HTTPConnector(
    url="http://financial_transactions_etl_json_server:3001/LEGACY_SYS"
)
manual_uploader_connector = HTTPConnector(
    url="http://financial_transactions_etl_json_server:3001/MANUAL_UPLOAD"
)
partner_feed_connector = HTTPConnector(
    url="http://financial_transactions_etl_json_server:3001/PARTNER_FEED"
)

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
def landing_zone(context) -> dg.MaterializeResult:
    landing_zone_controller.fetch_data()
    return dg.MaterializeResult()
