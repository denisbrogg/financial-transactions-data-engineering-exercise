import math
from enum import StrEnum
from typing import Any, ClassVar

from pipelines.logic.abstractions.silver.standardizer import Standardizer


class RiskProfile(StrEnum):
    CONSERVATIVE = "Conservative"
    GROWTH = "Growth"
    BALANCED = "Balanced"
    AGGRESSIVE = "Aggressive"


class AssetClass(StrEnum):
    EQUITY = "Equity"
    BOND = "Bond"
    FUND = "Fund"
    ETF = "ETF"
    CASH = "Cash"
    COMMODITY = "Commodity"
    REAL_ESTATE = "Real Estate"
    CRYPTO = "Crypto"


class TransactionType(StrEnum):
    BUY = "Buy"
    SELL = "Sell"
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    DIVIDEND = "Dividend"


class Currency(StrEnum):
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"


class CategoryNormalizer(Standardizer):
    """Canonicalizes categorical values using enum-backed categories."""

    COLUMN_ENUMS: ClassVar[dict[str, type[StrEnum]]] = {
        "risk_profile": RiskProfile,
        "asset_class": AssetClass,
        "transaction_type": TransactionType,
        "currency": Currency,
        "fee_currency": Currency,
    }

    COLUMN_ALIASES: ClassVar[dict[str, dict[str, StrEnum]]] = {
        "risk_profile": {
            "conservative": RiskProfile.CONSERVATIVE,
            "conservatve": RiskProfile.CONSERVATIVE,
            "growth": RiskProfile.GROWTH,
            "grwoth": RiskProfile.GROWTH,
            "balanced": RiskProfile.BALANCED,
            "balnced": RiskProfile.BALANCED,
            "aggressive": RiskProfile.AGGRESSIVE,
            "aggresive": RiskProfile.AGGRESSIVE,
        },
        "asset_class": {
            "equity": AssetClass.EQUITY,
            "equtiy": AssetClass.EQUITY,
            "eq": AssetClass.EQUITY,
            "stocks": AssetClass.EQUITY,
            "bond": AssetClass.BOND,
            "bnd": AssetClass.BOND,
            "fixed income": AssetClass.BOND,
            "fund": AssetClass.FUND,
            "mutual fund": AssetClass.FUND,
            "etf": AssetClass.ETF,
            "exchange traded fund": AssetClass.ETF,
            "cash": AssetClass.CASH,
            "commodity": AssetClass.COMMODITY,
            "commodities": AssetClass.COMMODITY,
            "real estate": AssetClass.REAL_ESTATE,
            "realestate": AssetClass.REAL_ESTATE,
            "property": AssetClass.REAL_ESTATE,
            "crypto": AssetClass.CRYPTO,
            "cryptocurrency": AssetClass.CRYPTO,
        },
        "transaction_type": {
            "buy": TransactionType.BUY,
            "b": TransactionType.BUY,
            "sell": TransactionType.SELL,
            "s": TransactionType.SELL,
            "deposit": TransactionType.DEPOSIT,
            "withdrawal": TransactionType.WITHDRAWAL,
            "dividend": TransactionType.DIVIDEND,
        },
        "currency": {
            "chf": Currency.CHF,
            "fr.": Currency.CHF,
            "sfr": Currency.CHF,
            "eur": Currency.EUR,
            "euro": Currency.EUR,
            "usd": Currency.USD,
            "us dollar": Currency.USD,
            "gbp": Currency.GBP,
        },
        "fee_currency": {
            "chf": Currency.CHF,
            "fr.": Currency.CHF,
            "sfr": Currency.CHF,
            "eur": Currency.EUR,
            "euro": Currency.EUR,
            "usd": Currency.USD,
            "us dollar": Currency.USD,
            "gbp": Currency.GBP,
        },
    }

    COLUMNS: ClassVar[list[str]] = [
        "risk_profile",
        "asset_class",
        "transaction_type",
        "currency",
        "fee_currency",
        "status",
        "channel",
        "source_system",
    ]

    def standardize_data(
        self, cleaned_record: dict[str, Any], standardized_record: dict[str, Any]
    ) -> None:
        for column in self.COLUMNS:
            source = (
                standardized_record if column in standardized_record else cleaned_record
            )
            raw_value: Any = source.get(column)

            if raw_value is None or (
                isinstance(raw_value, float) and math.isnan(raw_value)
            ):
                standardized_record[column] = None
                continue

            value = str(raw_value).strip()
            alias_map = self.COLUMN_ALIASES.get(column, {})
            canonical = alias_map.get(value.lower())
            if canonical is not None:
                standardized_record[column] = canonical.value
                continue

            enum_cls = self.COLUMN_ENUMS.get(column)
            if enum_cls is not None:
                try:
                    standardized_record[column] = enum_cls(value).value
                    continue
                except ValueError:
                    pass

            if column == "asset_class":
                known_asset_classes = {member.value for member in AssetClass}
                if standardized_record.get(column) not in known_asset_classes:
                    standardized_record[column] = None
                    continue

            standardized_record[column] = value
