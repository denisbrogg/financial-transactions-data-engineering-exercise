import unittest

from pipelines.logic.impl.silver.cleaners.typos import CategoryTypoCleaner
from pipelines.logic.impl.silver.normalizers.category_normalizer import (
    CategoryNormalizer,
)


class CategoryPipelineTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
