from fastapi import APIRouter, Body, Depends, status

from src import application as op
from src.infrastructure import Response, ResponseMulti, database, repositories

from ..contracts import Currency, CurrencyCreateBody

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.get("", status_code=status.HTTP_200_OK)
async def currencies(
    _=Depends(op.authorize),
) -> ResponseMulti[Currency]:
    """Return available cost categories."""

    currencies: tuple[database.Currency, ...] = (
        await repositories.Currency().currencies()
    )

    return ResponseMulti[Currency](
        result=[Currency.from_instance(item) for item in currencies]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def currency_create(
    _=Depends(op.authorize),
    body: CurrencyCreateBody = Body(...),
) -> Response[Currency]:
    """Create yet another equity."""

    repo = repositories.Currency()
    instance = await repo.add_currency(
        candidate=database.Currency(name=body.name, sign=body.sign)
    )
    await repo.flush()

    return Response[Currency](result=Currency.from_instance(instance))


@router.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def currency_delete(currency_id: int, _=Depends(op.authorize)) -> None:
    """Delete existing currency if does NOT have related transactions."""

    repo = repositories.Currency()
    await repo.delete_currency(currency_id=currency_id)
    await repo.flush()
