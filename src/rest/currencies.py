from fastapi import APIRouter, Body, status

from src import domain
from src.contracts import Currency, CurrencyCreateBody
from src.infrastructure import Response, ResponseMulti

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def currency_create(
    schema: CurrencyCreateBody = Body(...),
) -> Response[Currency]:
    """Create yet another currency."""

    instance: (
        domain.equity.CurrencyWithEquity
    ) = await domain.equity.EquityRepository().add_currency(
        candidate=domain.equity.CurrencyDBCandidate(
            name=schema.name, sign=schema.sign
        )
    )

    return Response[Currency](result=Currency.from_instance(instance))


@router.get("", status_code=status.HTTP_200_OK)
async def currencies() -> ResponseMulti[Currency]:
    """Return available cost categories."""

    return ResponseMulti[Currency](
        result=[
            Currency.from_instance(item)
            async for item in domain.equity.EquityRepository().currencies()
        ]
    )
