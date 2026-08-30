from abc import ABC, abstractmethod


class Connector(ABC):
    """Abstract class for all connectors"""

    @abstractmethod
    def fetch_data(self, landing_zone: str) -> None:
        """Fetch data from the source system and return a pandas DataFrame"""
