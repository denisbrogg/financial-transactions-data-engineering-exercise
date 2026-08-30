import math
from datetime import UTC, date, datetime
from typing import Any

from pipelines.logic.abstractions.silver.standardizer import Standardizer


class DateNormalizer(Standardizer):
    """Normalize supported transaction date formats to ISO date strings."""

    FORMATS = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
    )

    def standardize_data(
        self, cleaned_record: dict[str, Any], standardized_record: dict[str, Any]
    ) -> None:
        raw_value = (
            standardized_record["transaction_date"]
            if "transaction_date" in standardized_record
            else cleaned_record.get("transaction_date")
        )

        if raw_value is None or (
            isinstance(raw_value, float) and math.isnan(raw_value)
        ):
            standardized_record["transaction_date"] = None
            return

        if isinstance(raw_value, datetime):
            standardized_record["transaction_date"] = raw_value.date().isoformat()
            return
        if isinstance(raw_value, date):
            standardized_record["transaction_date"] = raw_value.isoformat()
            return

        value = str(raw_value).strip()
        if not value:
            standardized_record["transaction_date"] = None
            return

        for date_format in self.FORMATS:
            try:
                standardized_record["transaction_date"] = (
                    datetime.strptime(value, date_format)
                    .replace(tzinfo=UTC)
                    .date()
                    .isoformat()
                )
                return
            except ValueError:
                continue

        standardized_record["transaction_date"] = None
