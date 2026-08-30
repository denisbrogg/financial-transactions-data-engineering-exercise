from pathlib import Path

import pandas as pd

from pipelines.logic.abstractions.connector import Connector


class FullCSVConnector(Connector):
    """Full CSV connector"""

    def __init__(self, source_path: str):
        self.source_path = source_path

    def fetch_data(self, landing_zone: str) -> None:
        """Fetch data from the source system and return a pandas DataFrame"""

        df = pd.read_csv(self.source_path)
        landing_zone_path = Path(landing_zone)
        landing_zone_path.mkdir(parents=True, exist_ok=True)
        df.to_csv(landing_zone_path / "full_csv_data_source_fetch.csv", index=False)
