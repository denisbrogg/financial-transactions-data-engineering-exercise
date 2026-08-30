from abc import ABC, abstractmethod


class Ingestor(ABC):
    @abstractmethod
    def ingest_data(self, bronze_layer: str):
        """Ingest data into the bronze layer from fetched artifacts in the Landing Zone"""
