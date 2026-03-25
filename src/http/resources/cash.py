from fastapi import APIRouter, Body, Depends, status

from src import application as op
from src import domain
from src.infrastructure import Response, ResponseMulti

from ..contracts.cash import (
    CashBalance,
    CashBalanceCreateBody,
    CashBalanceUpdateBody,
)

router = APIRouter(prefix="/cash", tags=["Cash"])


@router.get("")
async def cash_balances(
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[CashBalance]:
    """Get all cash balance cards."""

    items = await op.get_cash_balances()

    return ResponseMulti[CashBalance](
        result=[CashBalance.from_instance(item) for item in items]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_cash_balance(
    _: domain.users.User = Depends(op.authorize),
    body: CashBalanceCreateBody = Body(...),
) -> Response[CashBalance]:
    """Add a new cash balance card."""

    item = await op.add_cash_balance(
        currency_id=body.currency_id,
        step=body.step_in_cents,
    )

    return Response[CashBalance](result=CashBalance.from_instance(item))


@router.patch("/{cash_balance_id}")
async def update_cash_balance(
    cash_balance_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: CashBalanceUpdateBody = Body(...),
) -> Response[CashBalance]:
    """Update balance and/or step of a cash card."""

    fields: dict = {}
    if body.balance_in_cents is not None:
        fields["balance"] = body.balance_in_cents
    if body.step_in_cents is not None:
        fields["step"] = body.step_in_cents

    if not fields:
        raise ValueError("Nothing to update")

    item = await op.update_cash_balance(
        cash_balance_id=cash_balance_id,
        **fields,
    )

    return Response[CashBalance](result=CashBalance.from_instance(item))


@router.delete(
    "/{cash_balance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_cash_balance(
    cash_balance_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """Remove a cash balance card."""

    await op.delete_cash_balance(cash_balance_id=cash_balance_id)
