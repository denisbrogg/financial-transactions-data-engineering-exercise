import unittest

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


if __name__ == "__main__":
    unittest.main()
