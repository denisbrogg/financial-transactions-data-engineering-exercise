from pathlib import Path

import duckdb

from pipelines.logic.abstractions.ingestor import Ingestor


class FullCSVIngestor(Ingestor):
    """Load the full CSV landing-zone artifact into DuckDB bronze storage."""

    artifact_name = "full_csv_data_source_fetch.csv"

    def __init__(self, source: str):
        self.source = Path(source)

    def ingest_data(self, sink: str) -> None:

        artifact_path = str(self.source / self.artifact_name)
        Path(sink).parent.mkdir(parents=True, exist_ok=True)

        with duckdb.connect(sink) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
            connection.execute(
                """
                CREATE OR REPLACE TEMP TABLE incoming_transactions AS
                SELECT *
                FROM read_csv_auto(?, header = true)
                """,
                [str(artifact_path)],
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bronze."transaction" AS
                SELECT * FROM incoming_transactions WHERE false
                """
            )
            connection.execute(
                """
                INSERT INTO bronze."transaction"
                SELECT incoming.* EXCLUDE (row_number)
                FROM (
                    SELECT *, row_number() OVER (
                        PARTITION BY transaction_id ORDER BY transaction_id
                    ) AS row_number
                    FROM incoming_transactions
                ) AS incoming
                WHERE incoming.row_number = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM bronze."transaction" AS existing
                      WHERE existing.transaction_id = incoming.transaction_id
                  )
                """
            )
