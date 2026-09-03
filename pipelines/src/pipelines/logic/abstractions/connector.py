from abc import ABC, abstractmethod

from .storage import Storage


class Connector(ABC):
    """A connector is an object that fetches data from a source and stores it via sink."""

    @abstractmethod
    def fetch_data(self, sink: Storage) -> str:
        """Fetch data from the source system and return artifact location of the sink"""
