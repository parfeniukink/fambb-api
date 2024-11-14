from datetime import date

from pydantic import Field

from src.domain.equity import Currency
from src.infrastructure import InternalData

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


# ==================================================
# analytics section
# ==================================================
class CostsByCategory(InternalData):
    """
    args:
        ``name`` - the name of the cost category
        ``total`` - the total for the selected category
    """

    name: str
    total: int
    ratio: float


class CostsAnalytics(InternalData):
    """represents relative numbers for costs by their categories.

    args:
        ``total`` - sum of all the categories costs
    """

    by_category: list[CostsByCategory] = Field(default_factory=list)
    total: int = 0


class IncomesBySource(InternalData):
    """
    args:
        ``source`` - the source of the income
        ``total`` - total by source

    todo:
        [ ] for the 'exchange' operation type expect only the ``to_value``
            in the analytics of the selected currency.

    notes:
        if the 'exchange' item is in the list - the operation type is revenue.
    """

    source: IncomeSource
    total: int


class IncomesAnalytics(InternalData):
    """just aggregates the data.

    args:
        ``total`` - the total of all incomes of all the sourcces
    """

    total: int = 0
    by_source: list[IncomesBySource] = Field(default_factory=list)


class TransactionsBasicAnalytics(InternalData):
    """represents the analytics aggregated block by the currency.

    args:
        ``from_exchanges`` - absolute value in the range for the
            selected currency. it you got 100$ and gave 50$ in exchange
            process, the value would be 50 (because 100 - 50)
    """

    currency: Currency
    costs: CostsAnalytics = CostsAnalytics()
    incomes: IncomesAnalytics = IncomesAnalytics()
    from_exchanges: int = 0

    @property
    def total_ratio(self) -> float:
        """all the 'inbounds incomes' to all the 'outbounds expences'.

        notes:
            outbounds = sum of all the costs totals
            inbounds = sum of all the incomes totals

        workflow:
            if inbounds is negative - 100% of ratio (all are costs)
        """

        inbounds = self.incomes.total + self.from_exchanges
        outbounds = self.costs.total

        if inbounds <= 0:
            return 100.0

        try:
            result = outbounds / inbounds * 100
        except ZeroDivisionError:
            return 100.0
        else:
            return result
