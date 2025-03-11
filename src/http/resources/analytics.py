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

from ..contracts.analytics import (
    AnalyticsPeriodQuery,
    TransactionBasicAnalytics,
)
from ..contracts.equity import Equity
from ..contracts.transactions import Transaction

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
async def transaction_basic_analytics(
    period: Annotated[
        AnalyticsPeriodQuery | None,
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
        user can specify either start date & end date or the 'period'.
        user can specify the pattern which is NOT CASE-SENSITIVE to filter
        by that name in cost name of income name.

    ERRORS CONDITIONS:
        ``period`` and any ``date`` are specified
        only one date is specified
        unrecognized period is specified
        nothing is specified

    NOTES:
        if the ``pattern`` is specified you WON'T see
            EXCHANGES in your analytics.
    """

    if start_date is not None and end_date is not None:
        if period is not None:
            raise ValueError(
                "you can't specify dates and period simultaneously"
            )
        else:
            # get instances by specified start and end dates
            instances: tuple[
                domain.transactions.TransactionsBasicAnalytics, ...
            ] = await domain.transactions.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                start_date=start_date, end_date=end_date, pattern=pattern
            )

    elif pattern is not None:
        # get instances by specified pattern
        instances = await domain.transactions.TransactionRepository().transactions_basic_analytics(  # noqa: E501
            pattern=pattern
        )
    else:
        if any((start_date, end_date)):
            raise ValueError("the range requires both dates to be specified")
        else:
            # get instances by period
            if period == "current-month":
                instances = await domain.transactions.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                    start_date=dates.get_first_date_of_current_month(),
                    end_date=date.today(),
                )
            elif period == "previous-month":
                start_date, end_date = dates.get_previous_month_range()
                instances = await domain.transactions.TransactionRepository().transactions_basic_analytics(  # noqa: E501
                    start_date=start_date, end_date=end_date
                )
            else:
                raise ValueError(f"Unavailable period: {period}")

    return ResponseMulti[TransactionBasicAnalytics](
        result=[
            TransactionBasicAnalytics.from_instance(instance)
            for instance in instances
        ]
    )
