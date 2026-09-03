import unittest
from unittest.mock import patch

from pipelines.defs.assets import api_feed_connector, storage
from pipelines.logic.impl.connectors.http_api_connector import HTTPConnector
from pipelines.logic.impl.silver.cleaners.numeric import NumericCleaner
from pipelines.logic.impl.silver.cleaners.typos import CategoryTypoCleaner
from pipelines.logic.impl.silver.normalizers.category_normalizer import (
    CategoryNormalizer,
)
from pipelines.logic.impl.silver.normalizers.date_normalizer import DateNormalizer


class CategoryPipelineTests(unittest.TestCase):
    def test_date_normalizer_converts_supported_formats_to_iso(self):
        normalizer = DateNormalizer()

        for raw_value, expected in {
            "2022-07-20": "2022-07-20",
            "23/05/2023": "2023-05-23",
            "12/27/2024": "2024-12-27",
            "27.07.2022": "2022-07-27",
            "16-Jul-2024": "2024-07-16",
            "": None,
        }.items():
            standardized = {}
            normalizer.standardize_data({"transaction_date": raw_value}, standardized)
            self.assertEqual(standardized["transaction_date"], expected)

    def test_typo_cleaner_corrects_actual_errors_but_not_formatting(self):
        bronze = {
            "risk_profile": "Aggresive",
            "asset_class": "Bnd",
            "transaction_type": "B",
            "currency": "US Dollar",
            "fee_currency": "Fr.",
        }
        cleaned = {}

        CategoryTypoCleaner().clean_data(bronze, cleaned)

        self.assertEqual(cleaned["risk_profile"], "Aggressive")
        self.assertEqual(cleaned["asset_class"], "Bond")
        self.assertEqual(cleaned["transaction_type"], "Buy")
        self.assertEqual(cleaned["currency"], "USD")
        self.assertEqual(cleaned["fee_currency"], "CHF")

    def test_normalizer_applies_canonical_format_after_typo_cleaning(self):
        bronze = {
            "risk_profile": "aggressive",
            "asset_class": "etf",
            "transaction_type": "buy",
            "currency": "usd",
            "fee_currency": "eur",
        }
        cleaned = dict(bronze)
        standardized = {}

        CategoryTypoCleaner().clean_data(bronze, cleaned)
        CategoryNormalizer().standardize_data(cleaned, standardized)

        self.assertEqual(standardized["risk_profile"], "Aggressive")
        self.assertEqual(standardized["asset_class"], "ETF")
        self.assertEqual(standardized["transaction_type"], "Buy")
        self.assertEqual(standardized["currency"], "USD")
        self.assertEqual(standardized["fee_currency"], "EUR")

    def test_numeric_cleaner_handles_mixed_locale_formats_and_signed_values(self):
        bronze = {
            "quantity": "-202.56",
            "price_per_unit": " 1.234,56 ",
            "gross_amount": "39.078,22",
            "fee": "8,03",
        }

        cleaned = {}
        NumericCleaner().clean_data(bronze, cleaned)

        self.assertEqual(cleaned["quantity"], "-202.56")
        self.assertEqual(cleaned["price_per_unit"], "1234.56")
        self.assertEqual(cleaned["gross_amount"], "39078.22")
        self.assertEqual(cleaned["fee"], "8.03")

    def test_assets_use_a_single_base_url_without_double_scheme(self):
        self.assertEqual(api_feed_connector.url, "http://localhost:3001/API_FEED")

    def test_storage_uses_project_data_directory(self):
        self.assertTrue(storage._root.endswith("/data"))

    def test_http_connector_writes_json_as_bytes(self):
        class DummyResponse:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        class DummySink:
            def __init__(self):
                self.path = None
                self.data = None

            def write(self, path, data):
                self.path = path
                self.data = data

        sink = DummySink()
        connector = HTTPConnector("http://localhost:3001/API_FEED")

        with patch(
            "pipelines.logic.impl.connectors.http_api_connector.httpx.get"
        ) as mocked_get:
            mocked_get.return_value = DummyResponse([{"id": 1, "account": "A"}])
            connector.fetch_data(sink)

        self.assertEqual(sink.path, "landing_zone/API_FEED.json")
        self.assertEqual(sink.data, b'[{"id": 1, "account": "A"}]')


if __name__ == "__main__":
    unittest.main()
