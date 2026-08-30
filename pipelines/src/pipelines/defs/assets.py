import os
from pathlib import Path

import dagster as dg
import pandas as pd
from dagster_duckdb import DuckDBResource

from pipelines.lib.foo import Bar

data_root = Path(os.getenv("DATA_ROOT", "/data"))
sample_data_file = data_root / "landing_zone" / "sample_data.csv"
processed_data_file = data_root / "landing_zone" / "processed_data.csv"


@dg.asset
def processed_data(context) -> pd.DataFrame:
    ## Read data from the CSV
    df = pd.read_csv(sample_data_file)

    ## Add an age_group column based on the value of age
    df["age_group"] = pd.cut(
        df["age"], bins=[0, 30, 40, 100], labels=["Young", "Middle", "Senior"]
    )

    ## Save processed data
    df.to_csv(processed_data_file, index=False)

    context.add_output_metadata(
        {
            "num_rows": len(df),
            "preview": df.head(10).to_json(orient="records"),
        }
    )

    return df


@dg.asset(deps=["processed_data"])
def exported_data(context, processed_data: pd.DataFrame, duckdb: DuckDBResource):
    table_name = "people"

    _ = Bar()

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create or replace table {table_name} as (
                select * from processed_data
            )
            """
        )
