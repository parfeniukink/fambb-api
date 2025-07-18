from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from src.domain.equity import Currency
from src.infrastructure import IncomeSource, InternalData

# represents the available list of query strings that client
# can specify instead of dates to get the basic analytics.
AnalyticsPeriod = Literal["current-month", "previous-month"]

OperationType = Literal["cost", "income", "exchange"]


class Transaction(InternalData):
    """represents the data structure across multiple database
    tables: 'incomes', 'costs', 'exchanges'.

    params:
        ``id`` the id of the cost or income or exchange.
        ``currency`` stands for the 'currency sign'. Ex: $, etc.
        ``icon`` is just a sign of an transaction.
                for costs - first character of category
                for incomes and exchanges - specific characters.

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
    icon: str
    name: str
    value: int
    timestamp: date
    currency: Currency
    user: str


class TransactionsFilter(InternalData):
    """this class is used to encapsulate filters for transactions fetching.

    ARGS:
        - currency_id
        - cost_category_id
        - start_date
        - end_date
        - period
        - operation
    """

    currency_id: int | None = None
    cost_category_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    period: AnalyticsPeriod | None = None
    operation: OperationType | None = None

    @model_validator(mode="after")
    def validate_dates_range(self):
        dates_range_specified: bool = bool(self.start_date and self.end_date)

        if dates_range_specified and self.period:
            raise ValueError("You can NOT specify DATES RANGE and PERIOD")

        # todo: add more validation

        return self


# ==================================================
# analytics section
# ==================================================
class CostsByCategory(InternalData):
    """
    args:
        ``id`` - the ID of the cost category
        ``name`` - the name of the cost category
        ``total`` - the total for the selected category
        ``ratio`` - total / all costs total
    """

    id: int
    name: str
    total: int
    ratio: float


class CostsAnalytics(InternalData):
    """represents relative numbers for costs by their categories.

    args:
        ``total`` - sum of all the categories costs
    """

    categories: list[CostsByCategory] = Field(default_factory=list)
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
    sources: list[IncomesBySource] = Field(default_factory=list)


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
            if inbounds <=0, then ratio = 100% (all are costs)
            append ``from_exchanges`` to ``incomes.total`` only in case
                the value > 0. otherwise it means selling money which
                neven means that it is a real cost.
        """

        inbounds = (
            (self.incomes.total + self.from_exchanges)
            if self.from_exchanges > 0
            else self.incomes.total
        )
        outbounds = self.costs.total

        if inbounds <= 0:
            return 100.0

        try:
            result: float = outbounds / inbounds * 100
        except ZeroDivisionError:
            return 100.0
        else:
            return result
