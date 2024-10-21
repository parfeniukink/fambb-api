"""
this module includes all the data structures of transactions.

data structures:
    - Transaction
    - Income
    - Cost
    - CostCategory
    - Exchange

notes:
    the ``src.domain.equity`` is not used from 'Bounded Context'
    for the simplicity.
"""

from datetime import date

from src.domain.equity import Currency
from src.infrastructure import InternalData, errors

from .types import IncomeSource, OperationType


class Transaction(InternalData):
    """represents the data structure across multiple database
    tables: 'incomes', 'costs', 'exchanges'.

    params:
        ``id`` the id of the cost or income or exchange.
        ``currency`` stands for the 'currency sign'. Ex: $, etc.

    notes:
        for the``exchange`` type of operation, the ``currency`` belongs
        to the ``exchanges.to_currency`` database parameter.
        the value that is going to be used is a sign of that currency.

        there is no reason to keep the ``id`` since they will be probably
        duplicated for different types of operations. nevertheless this
        is kept as 'Entity' instead of an 'Value object'.

        the ``id`` IS NOT unique.
    """

    id: int
    operation: OperationType
    name: str
    value: int
    timestamp: date
    currency: Currency


class Income(InternalData):
    id: int
    name: str
    value: int
    timestamp: date
    source: IncomeSource

    user_id: int
    currency: Currency


class CostCategory(InternalData):
    id: int
    name: str


class Cost(InternalData):
    id: int
    name: str
    value: int
    timestamp: date

    user_id: int
    currency: Currency
    category: CostCategory


class Exchange(InternalData):
    """``Exchange`` data structure represents the 'currency exchange' operation

    [example]
    John exchange 100 USD to UAH. price: 40UAH for 1USD.
    in that case the value of the operation = 100*40=4000

    params:
        ``from_currency`` - USD from example
        ``to_currency`` - UAH from example
        ``value`` - 4000
    """

    id: int
    from_value: int
    to_value: int
    timestamp: date

    user_id: int
    from_currency: Currency
    to_currency: Currency
