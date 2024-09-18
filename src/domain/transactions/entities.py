from datetime import datetime
from typing import Literal

from pydantic import field_validator

from src.domain.finances import Currency, CurrencyWithEquity
from src.infrastructure import InternalData

# ------------------------------------------------------------------
# transaction section
# ------------------------------------------------------------------
OperationType = Literal["cost", "income", "exchange"]
IncomeSource = Literal["revenue", "other", "gift", "debt"]


class Transaction(InternalData):
    """Represents the data structure across multiple database
    tables: 'incomes', 'costs', 'exchanges'

    Params:
        ``currency`` stands for the 'currency sign'. Ex: $, etc.

    Notes:
        For the``exchange`` type of operation, the ``currency`` belongs
        to the ``exchanges.to_currency`` database parameter.
        The value that is going to be used is a sign of that currency.

        There is no reason to keep the ``id`` since they will be probably
        duplicated for different types of operations. Nevertheless this
        is kept as 'Entity' instead of an 'Value object'.
    """

    name: str
    value: int
    currency: Currency
    operation: OperationType


# ------------------------------------------------------------------
# income section
# ------------------------------------------------------------------
class IncomeFlat(InternalData):
    """The 'income' database record representation."""

    id: int
    value: int
    timestamp: datetime
    name: str
    source: IncomeSource
    user_id: int
    currency_id: int


class Income(InternalData):
    """Aggregate."""

    id: int
    value: int
    timestamp: datetime
    name: str
    source: IncomeSource

    currency: Currency
    user_id: int


# ------------------------------------------------------------------
# cost section
# ------------------------------------------------------------------
class CostCateogoryFlat(InternalData):
    """The 'cost_category' database record representation."""

    id: int
    name: str


class CostFlat(InternalData):
    """The 'cost' database record representation."""

    id: int
    value: int
    timestamp: datetime
    name: str
    currency_id: int
    category_id: int


class Cost(InternalData):
    """Aggregate."""

    id: int
    name: str
    value: int
    timestamp: datetime

    user_id: int
    currency: Currency
    category: CostCateogoryFlat


# ------------------------------------------------------------------
# currency exchange section
# ------------------------------------------------------------------
class ExchangeFlat(InternalData):
    """The 'exchange_rate' database record representation."""

    id: int
    value: int
    timestamp: datetime
    from_currency_id: int
    to_currency_id: int


class Exchange(InternalData):
    """Aggregate."""

    id: int
    value: int
    timestamp: datetime

    user_id: int
    from_currency: Currency
    to_currency: Currency
