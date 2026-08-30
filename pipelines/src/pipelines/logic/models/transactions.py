from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    transaction_id: str
    source_system: str
    client_id: str
    client_name: str
    client_country: str | None = None
    risk_profile: str | None = None
    advisor_id: str | None = None
    advisor_name: str | None = None
    channel: str | None = None
    portfolio_id: str | None = None
    transaction_date: date | None = None
    asset_class: str | None = None
    instrument_name: str | None = None
    isin: str | None = None
    transaction_type: str | None = None
    quantity: Decimal | None = None
    price_per_unit: Decimal | None = None
    currency: str | None = None
    gross_amount: Decimal | None = None
    fee: Decimal | None = None
    fee_currency: str | None = None
    status: str | None = None
    notes: str | None = None

    @field_validator("transaction_date", mode="before")
    @classmethod
    def parse_transaction_date(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()

        value_str = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value_str, fmt).replace(tzinfo=UTC).date()
            except ValueError:
                continue

        return value

    @field_validator("quantity", "price_per_unit", "gross_amount", "fee", mode="before")
    @classmethod
    def parse_decimal_fields(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return value

        cleaned = str(value).strip().replace(",", "").replace(" ", "")
        if cleaned in {"", "None", "nan"}:
            return None
        return Decimal(cleaned)
