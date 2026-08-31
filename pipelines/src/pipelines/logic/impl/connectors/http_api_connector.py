import httpx

from pipelines.logic.abstractions.connector import Connector
from pipelines.logic.abstractions.storage import Storage


class HTTPConnector(Connector):
    """A connector that fetches data from an HTTP API and stores it via sink."""

    def __init__(self, url: str):
        self.url = url
        self.name = url.split("/")[-1]

    def fetch_data(self, sink: Storage) -> None:
        """Fetch data from the HTTP API and store it via sink."""
        response = httpx.get(self.url, timeout=30)
        response.raise_for_status()
        sink.write(path=f"landing_zone/{self.name}.json", data=response.json())
