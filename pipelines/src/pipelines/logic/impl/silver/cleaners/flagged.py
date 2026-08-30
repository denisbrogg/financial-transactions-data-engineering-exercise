from __future__ import annotations

from typing import Any

from pipelines.logic.abstractions.silver.cleaner import Cleaner


class FlaggedTransactionCleaner(Cleaner):
    """Marks suspiciously large transaction amounts and stores explicit flags."""

    OUTLIER_AMOUNT_THRESHOLD = 100_000_000
    FLAG_REASON = "gross_amount_exceeds_100m"

    def clean_data(
        self, bronze_record: dict[str, Any], cleaned_record: dict[str, Any]
    ) -> None:
        current_value = cleaned_record.get("gross_amount")
        if current_value is None:
            current_value = bronze_record.get("gross_amount")

        if current_value is None:
            cleaned_record["is_flagged"] = False
            return

        try:
            numeric_value = float(current_value)
        except (TypeError, ValueError):
            cleaned_record["is_flagged"] = False
            return

        flagged = numeric_value > self.OUTLIER_AMOUNT_THRESHOLD
        cleaned_record["is_flagged"] = flagged

        if flagged:
            cleaned_record["status"] = "flagged"
            cleaned_record["notes"] = (
                f"{cleaned_record.get('notes') or ''} | {self.FLAG_REASON}".strip(" |")
            )
