from abc import ABC, abstractmethod
from typing import Any


class Standardizer(ABC):
    """Abstract class for all standardizers."""

    @abstractmethod
    def standardize_data(
        self, cleaned_record: dict[str, Any], standardized_record: dict[str, Any]
    ) -> None:
        """Standardize one cleaned record in place."""
