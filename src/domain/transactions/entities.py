from datetime import datetime

from src.domain.equity import Currency
from src.infrastructure import InternalData

from .constants import IncomeSource, OperationType


# ------------------------------------------------------------------
# transaction section
# ------------------------------------------------------------------
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
class IncomeDBCandidate(InternalData):
    name: str
    value: int
    timestamp: datetime
    source: IncomeSource

    user_id: int
    currency_id: int


class IncomeFlat(IncomeDBCandidate):
    """The 'income' database record representation."""

    id: int


class Income(InternalData):
    """Aggregate."""

    id: int
    name: str
    value: int
    timestamp: datetime
    source: IncomeSource

    user_id: int
    currency: Currency


# ------------------------------------------------------------------
# cost section
# ------------------------------------------------------------------
class CostCategory(InternalData):
    id: int
    name: str


class CostDBCandidate(InternalData):
    name: str
    value: int
    timestamp: datetime

    user_id: int
    currency_id: int
    category_id: int


class CostFlat(CostDBCandidate):
    """The 'cost' database record representation."""

    id: int


class Cost(InternalData):
    """Aggregate."""

    id: int
    name: str
    value: int
    timestamp: datetime

    user_id: int
    currency: Currency
    category: CostCategory


# ------------------------------------------------------------------
# currency exchange section
# ------------------------------------------------------------------
class ExchangeDBCandidate(InternalData):
    value: int
    timestamp: datetime

    user_id: int
    from_currency_id: int
    to_currency_id: int


class ExchangeFlat(ExchangeDBCandidate):
    """The 'exchange_rate' database record representation."""

    id: int


class Exchange(InternalData):
    """Aggregate."""

    id: int
    value: int
    timestamp: datetime

    user_id: int
    from_currency: Currency
    to_currency: Currency
