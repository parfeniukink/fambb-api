"""
this module includes high-level operations to deal with transactions
analytics. instead of putting this to the ``./transactions.py``
this is separated to have cleaner code.
"""

from datetime import date

from src.domain import transactions as domain
from src.infrastructure import dates


async def transactions_basic_analytics(
    period: domain.AnalyticsPeriod | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    pattern: str | None = None,
) -> tuple[domain.TransactionsBasicAnalytics, ...]:
    """return basic transaction analytics."""

    if start_date is not None and end_date is not None:
        if period is not None:
            raise ValueError(
                "you can't specify dates and period simultaneously"
            )
        else:
            # get instances by specified start and end dates
            instances: tuple[
                domain.TransactionsBasicAnalytics, ...
            ] = await domain.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                start_date=start_date, end_date=end_date, pattern=pattern
            )

    elif pattern is not None:
        # get instances by specified pattern
        instances = await domain.TransactionRepository().transactions_basic_analytics(  # noqa: E501
            pattern=pattern
        )
    else:
        if any((start_date, end_date)):
            raise ValueError("the range requires both dates to be specified")
        else:
            # get instances by period
            if period == "current-month":
                instances = await domain.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                    start_date=dates.get_first_date_of_current_month(),
                    end_date=date.today(),
                )
            elif period == "previous-month":
                start_date, end_date = dates.get_previous_month_range()
                instances = await domain.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                    start_date=start_date, end_date=end_date
                )
            else:
                raise ValueError(f"Unavailable period: {period}")
    return instances


async def transactions_chart_analytics(
    start_date: date, end_date: date
) -> tuple[domain.Transaction, ...]:

    raise NotImplementedError("Chart analytics is not ready yet")
