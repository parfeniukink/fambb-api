import asyncio

from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMultiPaginated,
    database,
    get_offset_pagination_params,
)

from ..contracts import Income, IncomeUpdateBody, IncomeCreateBody, Currency

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
        result=[Income.from_instance(item) for item in items],
        context=context,
        left=left,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_income(
    user: domain.users.User = Depends(op.authorize),
    body: IncomeCreateBody = Body(...),
) -> Response[Income]:
    """add income. side effect: the equity is increased."""

    item: database.Income = await op.add_income(
        name=body.name,
        value=body.value_in_cents,
        timestamp=body.timestamp,
        source=body.source,
        currency_id=body.currency_id,
        user_id=user.id,
    )

    return Response[Income](result=Income.from_instance(item))


@router.get("/{income_id}", status_code=status.HTTP_200_OK)
async def get_income(
    income_id: int, _: domain.users.User = Depends(op.authorize)
) -> Response[Income]:
    """retrieve an income."""

    async with database.transaction():
        instance = await domain.transactions.TransactionRepository().income(
            id_=income_id
        )

    return Response[Income](result=Income.from_instance(instance))


@router.patch("/{income_id}", status_code=status.HTTP_200_OK)
async def update_income(
    income_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: IncomeUpdateBody = Body(...),
) -> Response[Income]:
    """modify income.

    SIDE EFFECT
        equity is updated
    """

    payload = body.model_dump(exclude_unset=True)
    if _value := body.value_in_cents:
        payload |= {"value": _value}

    instance: database.Income = await op.update_income(
        income_id=income_id, **payload
    )

    return Response[Income](
        result=Income(
            id=instance.id,
            name=instance.name,
            value=instance.value,
            source=instance.source,
            currency=Currency.model_validate(instance.currency),
            timestamp=instance.timestamp,
            user=instance.user.name,
        )
    )


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """delete income.

    SIDE EFFECTS
        equity is decreased
    """

    await op.delete_income(income_id=income_id)
