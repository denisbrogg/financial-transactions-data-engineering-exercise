import json

import httpx

from pipelines.logic.abstractions.connector import Connector
from pipelines.logic.abstractions.storage import Storage


class HTTPConnector(Connector):
    """A connector that fetches data from an HTTP API and stores it via sink."""

    def __init__(self, url: str):
        self.url = url
        self.name = url.rstrip("/").split("/")[-1]

    def __str__(self) -> str:
        return f"HTTPConnector({self.url})"

    def fetch_data(self, sink: Storage) -> str:
        """Fetch data from the HTTP API and store it via sink."""
        response = httpx.get(self.url, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return sink.write(
            path=f"landing_zone/{self.name}.json",
            data=json.dumps(payload).encode("utf-8"),
        )
