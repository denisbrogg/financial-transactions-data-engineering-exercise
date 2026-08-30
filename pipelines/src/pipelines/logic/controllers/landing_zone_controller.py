import logging

from pipelines.logic.abstractions.connector import Connector

logger = logging.getLogger(__name__)


class LandingZoneController:
    """Fetch data from all datasource connectors into the landing zone."""

    def __init__(self, sink: str, connectors: list[Connector]):
        self.sink = sink
        self.connectors = connectors

    def fetch_data(self) -> None:
        """Fetch data from all connectors and store their raw artifacts."""
        logger.info("Populating landing zone")
        for connector in self.connectors:
            logger.info(f"Fetching data from connector: {connector.__class__.__name__}")
            connector.fetch_data(self.sink)
