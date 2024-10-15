from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src import contracts, domain
from src import operational as op
from src.infrastructure import (
    OffsetPagination,
    ResponseMulti,
    ResponseMultiPaginated,
    get_offset_pagination_params,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/", status_code=status.HTTP_200_OK)
async def charts(
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[contracts.Chart]:
    """Expose last transactions, not filtered but limited with Settings."""

    raise NotImplementedError


@router.get("/equity", status_code=status.HTTP_200_OK)
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


@router.get("/transactions", status_code=status.HTTP_200_OK)
async def transactions(
    currency_id: Annotated[
        int | None,
        Query(description="Filter by currency id. Skip to ignore.", alias="currencyId"),
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
