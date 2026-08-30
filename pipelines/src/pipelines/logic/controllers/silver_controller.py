import logging
from typing import Any

import duckdb
import pandas as pd

from pipelines.logic.abstractions.silver.cleaner import Cleaner
from pipelines.logic.abstractions.silver.deduplicator import Deduplicator
from pipelines.logic.abstractions.silver.standardizer import Standardizer

logger = logging.getLogger(__name__)


class SilverController:
    """Create silver curated data from bronze raw data."""

    def __init__(
        self,
        source: str,
        sink: str,
        cleaners: list[Cleaner],
        standardizers: list[Standardizer],
        deduplicators: list[Deduplicator],
    ):
        self.source = source
        self.sink = sink
        self.cleaners = cleaners
        self.standardizers = standardizers
        self.deduplicators = deduplicators

    def curate_transactions(
        self, raw_transactions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Curate data from bronze layer to silver layer."""
        logger.info("Curating data from bronze layer to silver layer")

        cleaned_transactions = []
        for bronze_record in raw_transactions:
            cleaned_record: dict[str, Any] = dict(bronze_record)
            for cleaner in self.cleaners:
                cleaner.clean_data(bronze_record, cleaned_record)
                bronze_record = cleaned_record
            cleaned_transactions.append(cleaned_record)

        standardized_transactions = []
        for cleaned_record in cleaned_transactions:
            standardized_record: dict[str, Any] = dict(cleaned_record)
            for standardizer in self.standardizers:
                standardizer.standardize_data(cleaned_record, standardized_record)
                cleaned_record = standardized_record
            standardized_transactions.append(standardized_record)

        final_transactions = standardized_transactions
        for deduplicator in self.deduplicators:
            final_transactions = deduplicator.deduplicate_data(final_transactions)

        self._store_transactions(final_transactions)
        return final_transactions

    def _store_transactions(self, transactions: list[dict[str, Any]]) -> None:
        """Append curated transactions to silver storage by transaction ID."""
        with duckdb.connect(self.sink) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS silver."transaction" AS
                SELECT * FROM bronze."transaction" WHERE false
                """
            )
            connection.execute(
                'ALTER TABLE silver."transaction" ADD COLUMN IF NOT EXISTS is_flagged BOOLEAN'
            )

            if not transactions:
                return

            connection.register("curated_transactions", pd.DataFrame(transactions))
            connection.execute(
                """
                INSERT INTO silver."transaction" BY NAME
                SELECT incoming.* EXCLUDE (row_number)
                FROM (
                    SELECT *, row_number() OVER (
                        PARTITION BY transaction_id ORDER BY transaction_id
                    ) AS row_number
                    FROM curated_transactions
                ) AS incoming
                WHERE incoming.row_number = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM silver."transaction" AS existing
                      WHERE existing.transaction_id = incoming.transaction_id
                  )
                """
            )
            connection.unregister("curated_transactions")
