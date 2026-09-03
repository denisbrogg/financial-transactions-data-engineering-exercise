import logging

from pipelines.logic.abstractions.ingestor import Ingestor
from pipelines.logic.abstractions.storage import Storage

logger = logging.getLogger(__name__)


class BronzeController:
    """Create bronze raw data from parsed assets in the Landing Zone"""

    def __init__(self, source: Storage, sink: Storage, ingestors: list[Ingestor]):
        self.source = source
        self.sink = sink
        self.ingestors = ingestors

    def ingest_data(self) -> None:
        """Ingest data from Landing Zone"""
        logger.info("Ingesting data from Landing Zone")
        for ingestor in self.ingestors:
            logger.info(f"Ingesting data from ingestor: {ingestor.__class__.__name__}")
            ingestor.ingest_data(self.source, self.sink)
