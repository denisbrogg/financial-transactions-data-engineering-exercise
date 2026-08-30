from __future__ import annotations

from abc import ABC, abstractmethod

import duckdb


class GoldTableLoader(ABC):
    """Load a gold table from the curated silver dataset."""

    @abstractmethod
    def load(self, connection: duckdb.DuckDBPyConnection) -> int:
        """Write all rows for one table into the gold layer and return the row count."""
