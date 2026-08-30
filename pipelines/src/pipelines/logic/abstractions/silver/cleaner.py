from abc import ABC, abstractmethod
from typing import Any


class Cleaner(ABC):
    """Abstract class for all cleaners"""

    @abstractmethod
    def clean_data(
        self, bronze_record: dict[str, Any], cleaned_record: dict[str, Any]
    ) -> None:
        """Clean one record into the supplied destination dictionary."""
