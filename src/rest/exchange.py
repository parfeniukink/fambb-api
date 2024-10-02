import asyncio

from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.contracts import Exchange, ExchangeCreateBody, ExchangeUpdateBody
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMultiPaginated,
    database,
    get_offset_pagination_params,
)

router = APIRouter(prefix="/exchange", tags=["Transactions", "Exchange"])


@router.get("")
async def exchanges(
    user: domain.users.User = Depends(op.authorize),
    pagination: OffsetPagination = Depends(get_offset_pagination_params),
) -> ResponseMultiPaginated[Exchange]:
    """get incomes."""

    tasks = (
        op.get_currency_exchanges(
            user_id=user.id, offset=pagination.context, limit=pagination.limit
        ),
        domain.transactions.TransactionRepository().count(database.Exchange),
    )

    items, total = await asyncio.gather(*tasks)

    if items:
        context: int = pagination.context + len(items)
        left: int = total - context
    else:
        context = 0
        left = 0

    return ResponseMultiPaginated[Exchange](
        result=[Exchange.model_validate(item) for item in items],
        context=context,
        left=left,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_exchange(
    user: domain.users.User = Depends(op.authorize),
    body: ExchangeCreateBody = Body(...),
) -> Response[Exchange]:
    """add exchange. side effect: the equity is updated for 2 currencies."""

    item: database.Exchange = await op.currency_exchange(
        from_value=body.from_value,
        to_value=body.to_value,
        timestamp=body.timestamp,
        from_currency_id=body.from_currency_id,
        to_currency_id=body.to_currency_id,
        user_id=user.id,
    )

    return Response[Exchange](result=Exchange.model_validate(item))


@router.delete("/{exchange_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange(
    exchange_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """delete exchange. side effect: the equity is decreased."""

    await op.delete_currency_exchange(item_id=exchange_id)


@router.patch("/{exchange_id}")
async def update_exchange(
    exchange_id: int,
    body: ExchangeUpdateBody = Body(...),
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """update exchange. side effect: the equity is decreased.

    notes:
        this feature is currently not available because of the complexity
        in the equity operations and the huge amount of tests that should
        be added to create a robust feature.
    """

    raise NotImplementedError("This feature is not available for the MVP")
