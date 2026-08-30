from abc import ABC, abstractmethod
from typing import Any


class Deduplicator(ABC):
    """Abstract class for all deduplicators."""

    @abstractmethod
    def deduplicate_data(
        self, cleaned_records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return records with duplicates removed."""
