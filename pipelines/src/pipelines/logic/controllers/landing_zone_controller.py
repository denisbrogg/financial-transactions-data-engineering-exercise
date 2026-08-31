import logging

from pipelines.logic.abstractions.connector import Connector
from pipelines.logic.abstractions.storage import Storage

logger = logging.getLogger(__name__)


class LandingZoneController:
    """Fetch data from all datasource connectors into the landing zone."""

    def __init__(self, connectors: list[Connector], sink: Storage):
        self.connectors = connectors
        self.sink = sink

    def fetch_data(self) -> None:
        """Fetch data from all connectors and store their raw artifacts."""
        logger.info(
            "Fetching from datasources started.",
            extra={
                "connectors": [c.__class__.__name__ for c in self.connectors],
                "sink": str(self.sink),
            },
        )
        for connector in self.connectors:
            logger.info(
                "Fetching data from connector",
                extra={"connector": connector.__class__.__name__},
            )
            connector.fetch_data(self.sink)
