from __future__ import annotations

from pathlib import Path

import duckdb

from pipelines.logic.abstractions.gold.table_loader import GoldTableLoader


class GoldController:
    """Controller for creating and populating the gold layer."""

    def __init__(
        self,
        source: str | None = None,
        sink: str | None = None,
        loaders: list[GoldTableLoader] | None = None,
        database_path: str | None = None,
    ):
        if sink is None and database_path is not None:
            sink = database_path
        if source is None:
            source = sink
        if sink is None:
            raise ValueError("GoldController requires a sink path or database_path")

        self.source = source
        self.sink = sink
        self.database_path = sink
        self.loaders = loaders or []
        self.schema_name = "gold"
        self.ddl_path = Path(__file__).resolve().parents[2] / "ddl" / "gold_schema.sql"

    def initialize_tables(self) -> None:
        Path(self.sink).parent.mkdir(parents=True, exist_ok=True)
        ddl_sql = self.ddl_path.read_text()
        with duckdb.connect(self.sink) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
            connection.execute(ddl_sql)

    def run_loaders(self) -> dict[str, int]:
        results: dict[str, int] = {}
        with duckdb.connect(self.sink) as connection:
            for loader in self.loaders:
                results[loader.__class__.__name__] = loader.load(connection)
        return results

    def load_dimension(self, loader: GoldTableLoader) -> int:
        with duckdb.connect(self.sink) as connection:
            return loader.load(connection)

    def load_fact(self, loader: GoldTableLoader) -> int:
        with duckdb.connect(self.sink) as connection:
            return loader.load(connection)
