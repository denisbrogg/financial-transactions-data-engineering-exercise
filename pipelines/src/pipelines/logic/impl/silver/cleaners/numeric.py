import math
from typing import Any, ClassVar

from pipelines.logic.abstractions.silver.cleaner import Cleaner


class NumericCleaner(Cleaner):
    """Normalize mixed European and US numeric formats before Decimal parsing."""

    NUMERIC_COLUMNS: ClassVar[set[str]] = {
        "quantity",
        "price_per_unit",
        "gross_amount",
        "fee",
    }

    def clean_data(
        self, bronze_record: dict[str, Any], cleaned_record: dict[str, Any]
    ) -> None:
        for column, value in bronze_record.items():
            if column not in self.NUMERIC_COLUMNS:
                cleaned_record[column] = value
                continue

            cleaned_record[column] = self._normalize_numeric_value(value)

        for column in self.NUMERIC_COLUMNS:
            if column not in bronze_record and column in cleaned_record:
                cleaned_record[column] = self._normalize_numeric_value(
                    cleaned_record[column]
                )

    def _normalize_numeric_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if isinstance(value, float) and math.isnan(value):
                return None
            return str(value)
        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if cleaned == "":
            return None

        normalized_lower = cleaned.lower()
        if normalized_lower in {"none", "nan", "null"}:
            return None

        sign = ""
        if cleaned.startswith("-"):
            sign = "-"
            cleaned = cleaned[1:]
        elif cleaned.startswith("+"):
            cleaned = cleaned[1:]

        cleaned = cleaned.replace(" ", "")
        if cleaned in {"", ".", ","}:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            if cleaned.count(",") > 1:
                parts = cleaned.split(",")
                if len(parts[-1]) == 3 and all(len(part) == 3 for part in parts[:-1]):
                    cleaned = "".join(parts)
                else:
                    if len(parts[-1]) in {1, 2}:
                        cleaned = ".".join(parts)
                    else:
                        cleaned = "".join(parts)
            else:
                left, right = cleaned.split(",", 1)
                if len(right) in {1, 2}:
                    cleaned = f"{left}.{right}"
                elif len(right) == 3 and left:
                    cleaned = f"{left}{right}"
                else:
                    cleaned = cleaned.replace(",", "")
        elif "." in cleaned and cleaned.count(".") > 1:
            parts = cleaned.split(".")
            if len(parts[-1]) == 3 and all(len(part) == 3 for part in parts[:-1]):
                cleaned = "".join(parts)

        if sign:
            cleaned = f"{sign}{cleaned}"
        return cleaned
