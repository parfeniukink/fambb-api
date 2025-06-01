from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src import domain
from src import operational as op
from src.infrastructure import (
    OffsetPagination,
    ResponseMulti,
    ResponseMultiPaginated,
    dates,
    get_offset_pagination_params,
)

from ..contracts import Equity, Transaction, TransactionBasicAnalytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/equity")
async def equity(
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Equity]:
    """expose the ``equity``, related to each currency."""

    return ResponseMulti[Equity](
        result=[
            Equity.from_instance(item)
            for item in await domain.equity.EquityRepository().currencies()
        ]
    )


# todo: move to the ``resources/transactions.py``
# reason: probably not the part of the analytics block at all
@router.get("/transactions")
async def transactions(
    currency_id: Annotated[
        int | None,
        Query(
            description="Filter by currency id. Skip to ignore.",
            alias="currencyId",
        ),
    ] = None,
    pagination: OffsetPagination = Depends(get_offset_pagination_params),
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMultiPaginated[Transaction]:
    """transactions list. includes costs, incomes and exchanges.

    Notes:
        the returned ``total`` value is based on applied filters.
        if the currency is specified - ``total`` might be changed
        so you can rely on data properly.
    """

    (
        items,
        total,
    ) = await domain.transactions.TransactionRepository().transactions(
        currency_id=currency_id,
        offset=pagination.context,
        limit=pagination.limit,
    )

    if items:
        context: int = pagination.context + len(items)
        left: int = total - context
    else:
        context = 0
        left = 0

    return ResponseMultiPaginated[Transaction](
        result=[Transaction.from_instance(item) for item in items],
        context=context,
        left=left,
    )


@router.get("/basic")
async def transaction_analytics_basic(
    period: Annotated[
        domain.transactions.AnalyticsPeriod | None,
        Query(description="specified period instead of start and end dates"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(
            description="the start date of transaction in the analytics",
            alias="startDate",
        ),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(
            description="the end date of transaction in the analytics",
            alias="endDate",
        ),
    ] = None,
    pattern: Annotated[
        str | None,
        Query(
            description="the pattern to filter results",
            alias="pattern",
        ),
    ] = None,
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[TransactionBasicAnalytics]:
    """basic analytics that supports a set of some filters.

    WORKFLOW:
        - user can specify either start date & end date or the 'period'.
        - user can specify the pattern which is NOT CASE-SENSITIVE to filter
            by that 'pattern' in 'cost name' or 'income name'.

    POSSIBLE ERRORS:
        - nothing is specified
        - 'period' and 'date' are specified
        - only a single date is specified (no range)
        - unrecognized period is specified

    NOTES:
        if the 'pattern' is specified you WON'T see EXCHANGES in your analytics
    """

    instances: tuple[domain.transactions.TransactionsBasicAnalytics, ...] = (
        await op.transactions_basic_analytics(
            period, start_date, end_date, pattern
        )
    )

    return ResponseMulti[TransactionBasicAnalytics](
        result=[
            TransactionBasicAnalytics.from_instance(instance)
            for instance in instances
        ]
    )


@router.get("/transactions/stream")
async def transaction_stream(
    start_date: Annotated[
        date,
        Query(
            description=(
                "the start date of transaction in the analytics. "
                "default value is the first day of the current year"
            ),
            alias="startDate",
            default_factory=dates.first_year_date,
        ),
    ],
    end_date: Annotated[
        date,
        Query(
            description="the end date of transaction in the analytics",
            alias="endDate",
            default_factory=date.today,
        ),
    ],
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Transaction]:
    """analytics charts for annual tracking. not implemented yet"""

    instances: tuple[domain.transactions.Transaction, ...] = (
        await op.transactions_chart_analytics(start_date, end_date)
    )

    return ResponseMulti[Transaction](
        result=[Transaction.from_instance(instance) for instance in instances]
    )
