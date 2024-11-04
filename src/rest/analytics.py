from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from src import contracts, domain
from src import operational as op
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMulti,
    ResponseMultiPaginated,
    database,
    dates,
    get_offset_pagination_params,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/equity")
async def equity(
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[contracts.Equity]:
    """Expose the ``equity``, related to each currency."""

    return ResponseMulti[contracts.Equity](
        result=[
            contracts.Equity.from_instance(item)
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
) -> ResponseMultiPaginated[contracts.Transaction]:
    """Expose transactions. Includes costs, incomes and exchanges.

    Notes:
        The returned ``total`` value is based on applied filters.
        If the currency is specified - ``total`` might be changed
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

    return ResponseMultiPaginated[contracts.Transaction](
        result=[contracts.Transaction.from_instance(item) for item in items],
        context=context,
        left=left,
    )


@router.get("/basic")
async def transaction_basic_analytics(
    period: Annotated[
        contracts.AnalyticsPeriodQuery | None,
        Query(description="Specified period instead of start and end dates"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(
            description="The start date of transaction in the analytics",
            alias="startDate",
        ),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(
            description="The end date of transaction in the analytics",
            alias="endDate",
        ),
    ] = None,
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[contracts.TransactionBasicAnalytics]:
    """Get the basic analytics of all kind of transactions.

    Workflow:
        User can specify either start date & end date or the 'period'.

    Errors conditions:
        - the 'period' and any 'date' are specified
        - only one date is specified
        - unrecognized period is specified
        - nothing is specified
    """

    if start_date is not None and end_date is not None:
        if period is not None:
            raise ValueError(
                "You can't specify dates and period simultaneously"
            )
        else:
            # get instances by specified start and end dates
            instances: tuple[
                domain.transactions.TransactionsBasicAnalytics, ...
            ] = await domain.transactions.TransactionRepository().transactions_basic_analytics(
                start_date=start_date, end_date=end_date
            )
    else:
        if any((start_date, end_date)):
            raise ValueError("The range requires both dates to be specified")
        if period is None:
            raise ValueError(
                "Please specify dates range or period for the basic analytics"
            )
        else:
            # get instances by period
            if period == "current-month":
                instances = await domain.transactions.TransactionRepository().transactions_basic_analytics(
                    start_date=dates.get_first_date_of_current_month(),
                    end_date=date.today(),
                )
            elif period == "previous-month":
                start_date, end_date = dates.get_previous_month_range()
                instances = await domain.transactions.TransactionRepository().transactions_basic_analytics(
                    start_date=start_date, end_date=end_date
                )
            else:
                raise ValueError(f"Unavailable period: {period}")

    return ResponseMulti[contracts.TransactionBasicAnalytics](
        result=[
            contracts.TransactionBasicAnalytics.from_instance(instance)
            for instance in instances
        ]
    )
