import math
from typing import Any, ClassVar

from pipelines.logic.abstractions.silver.cleaner import Cleaner


class CategoryTypoCleaner(Cleaner):
    """
    Fixes genuine misspellings only.
    Equivalent spellings, aliases, and formatting variants stay in the
    normalizer so the cleaner remains limited to true typo repair.
    """

    COLUMN_MAPS: ClassVar[dict[str, dict[str, str]]] = {
        "risk_profile": {
            "Conservatve": "Conservative",
            "Grwoth": "Growth",
            "Balnced": "Balanced",
            "Aggresive": "Aggressive",
        },
        "asset_class": {
            "Equtiy": "Equity",
            "Bnd": "Bond",
            "Commodities": "Commodity",
            "RealEstate": "Real Estate",
            "Cryptocurrency": "Crypto",
        },
        "transaction_type": {
            "B": "Buy",
            "S": "Sell",
        },
        "currency": {
            "Fr.": "CHF",
            "SFr": "CHF",
            "US Dollar": "USD",
            "Euro": "EUR",
        },
        "fee_currency": {
            "Fr.": "CHF",
            "SFr": "CHF",
            "US Dollar": "USD",
            "Euro": "EUR",
        },
    }

    def clean_data(self, bronze_record: dict, cleaned_record: dict) -> None:
        for column, lookup in self.COLUMN_MAPS.items():
            source = cleaned_record if column in cleaned_record else bronze_record
            raw_value: Any = source.get(column)

            if raw_value is None or (
                isinstance(raw_value, float) and math.isnan(raw_value)
            ):
                cleaned_record[column] = None
                continue

            cleaned_record[column] = lookup.get(raw_value, raw_value)


class HardcodedTypoCleaner(CategoryTypoCleaner):
    """Backward-compatible alias for the typo-only cleaner."""
