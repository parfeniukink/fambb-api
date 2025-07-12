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
from src.infrastructure import IncomeSource, InternalData


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
