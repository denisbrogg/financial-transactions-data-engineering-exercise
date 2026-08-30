from typing import Any

from pipelines.logic.abstractions.silver.cleaner import Cleaner


class SpacesCleaner(Cleaner):
    """Strip leading and trailing whitespace from string fields."""

    def clean_data(
        self, bronze_record: dict[str, Any], cleaned_record: dict[str, Any]
    ) -> None:
        for column, value in bronze_record.items():
            cleaned_record[column] = value.strip() if isinstance(value, str) else value
