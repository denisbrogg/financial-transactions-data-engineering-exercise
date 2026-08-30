from typing import Any

from pipelines.logic.abstractions.silver.cleaner import Cleaner


class EncodingCleaner(Cleaner):
    """Replace undecodable text markers in string fields."""

    def clean_data(
        self, bronze_record: dict[str, Any], cleaned_record: dict[str, Any]
    ) -> None:
        for column, value in bronze_record.items():
            if isinstance(value, str):
                cleaned_record[column] = value.encode("utf-8", "replace").decode(
                    "utf-8"
                )
            else:
                cleaned_record[column] = value
