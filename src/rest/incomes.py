import asyncio

from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.contracts import Income, IncomeCreateBody
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMultiPaginated,
    database,
    get_offset_pagination_params,
)

router = APIRouter(prefix="/incomes", tags=["Transactions", "Incomes"])


@router.get("")
async def incomes(
    user: domain.users.User = Depends(op.authorize),
    pagination: OffsetPagination = Depends(get_offset_pagination_params),
) -> ResponseMultiPaginated[Income]:
    """get incomes."""

    tasks = (
        op.get_incomes(
            user_id=user.id, offset=pagination.context, limit=pagination.limit
        ),
        domain.transactions.TransactionRepository().count(database.Income),
    )

    items, total = await asyncio.gather(*tasks)

    if items:
        context: int = pagination.context + len(items)
        left: int = total - context
    else:
        context = 0
        left = 0

    return ResponseMultiPaginated[Income](
        result=[Income.model_validate(item) for item in items],
        context=context,
        left=left,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_income(
    user: domain.users.User = Depends(op.authorize),
    body: IncomeCreateBody = Body(...),
) -> Response[Income]:
    """add income. side effect: the equity is decreased."""

    item: database.Income = await op.add_income(
        name=body.name,
        value=body.value,
        timestamp=body.timestamp,
        source=body.source,
        currency_id=body.currency_id,
        user_id=user.id,
    )

    return Response[Income](result=Income.model_validate(item))
