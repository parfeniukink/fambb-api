from fastapi import APIRouter, Body, status

from src import domain
from src import operations as op
from src.contracts import CostCategory, CostCategoryCreateBody
from src.infrastructure import Response, ResponseMulti

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/costs/categories", status_code=status.HTTP_200_OK)
async def costs_categories() -> ResponseMulti[CostCategory]:
    """Return available cost categories."""

    return ResponseMulti[CostCategory](
        result=[
            CostCategory.model_validate(item)
            async for item in domain.transactions.TransactionRepository().cost_categories()
        ]
    )


@router.post("/costs/categories", status_code=status.HTTP_200_OK)
async def costs_category_create(
    schema: CostCategoryCreateBody = Body(...),
) -> Response[CostCategory]:
    """Create a new cost category"""

    item: domain.transactions.CostCateogoryFlat = (
        await op.cost_category_create(schema.name)
    )

    return Response[CostCategory](result=CostCategory.model_validate(item))
