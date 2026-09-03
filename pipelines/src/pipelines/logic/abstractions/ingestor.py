from abc import ABC, abstractmethod

from pipelines.logic.abstractions.storage import Storage


class Ingestor(ABC):
    @abstractmethod
    def ingest_data(self, source: Storage, sink: Storage) -> None:
        """Ingest data into the bronze layer from fetched artifacts in the Landing Zone"""
