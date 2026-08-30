import os
from pathlib import Path

import dagster as dg
from dagster_duckdb import DuckDBResource

database_resource = DuckDBResource(
    database=str(Path(os.getenv("DATA_ROOT", "/data")) / "db" / "transactions.duckdb")
)


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "duckdb": database_resource,
        }
    )
