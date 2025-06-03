from datetime import date
from typing import Annotated

from fastapi import Query

from src.domain.transactions import (
    AnalyticsPeriod,
    OperationType,
    TransactionsFilter,
)


def get_transactions_detail_filter(
    currency_id: Annotated[
        int | None,
        Query(
            description="Filter by currency id. Skip to ignore.",
            alias="currencyId",
        ),
    ] = None,
    cost_category_id: Annotated[
        int | None,
        Query(
            description="Filter by cost_category id. Skip to ignore.",
            alias="costCategoryId",
        ),
    ] = None,
    period: Annotated[
        AnalyticsPeriod | None,
        Query(
            description="Alias for start/end dates.",
            alias="period",
        ),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(
            description=(
                "the start date of transaction in the analytics. "
                "default value is the first day of the current year"
            ),
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
    operation: Annotated[
        OperationType | None,
        Query(description="the type of the operation. skip to ommit"),
    ] = None,
) -> TransactionsFilter:
    """FastAPI HTTP GET query params.

    usage:
        ```py
        @router.get("")
        async def controller(
            pagination: TransactionsDetailFilter = fastapi.Depends(
                get_transactions_detail_filter
            )
        ):
            ...
    """

    return TransactionsFilter(
        currency_id=currency_id,
        cost_category_id=cost_category_id,
        period=period,
        start_date=start_date,
        end_date=end_date,
        operation=operation,
    )
