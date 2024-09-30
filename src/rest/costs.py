import asyncio

from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.contracts import (
    Cost,
    CostCategory,
    CostCategoryCreateBody,
    CostCreateBody,
)
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMulti,
    ResponseMultiPaginated,
    database,
    get_cursor_pagination_params,
)

router = APIRouter(prefix="/costs", tags=["Costs"])


@router.get("/categories", status_code=status.HTTP_200_OK)
async def cost_categories(
    _=Depends(op.authorize),
) -> ResponseMulti[CostCategory]:
    """return available cost categories from the database."""

    return ResponseMulti[CostCategory](
        result=[
            CostCategory.model_validate(item)
            async for item in domain.transactions.TransactionRepository().cost_categories()
        ]
    )


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def cost_category_create(
    _=Depends(op.authorize),
    schema: CostCategoryCreateBody = Body(...),
) -> Response[CostCategory]:
    """create a new cost category."""

    async with database.transaction():
        item: (
            database.CostCategory
        ) = await domain.transactions.TransactionRepository().add_cost_category(
            candidate=database.CostCategory(name=schema.name)
        )

    return Response[CostCategory](result=CostCategory.model_validate(item))


@router.get("", status_code=status.HTTP_200_OK)
async def costs(
    user: domain.users.User = Depends(op.authorize),
    pagination: OffsetPagination = Depends(get_cursor_pagination_params),
) -> ResponseMultiPaginated[Cost]:
    """get costs."""

    tasks = (
        op.get_costs(
            user_id=user.id, offset=pagination.context, limit=pagination.limit
        ),
        domain.transactions.TransactionRepository().count(database.Cost),
    )

    items, total = await asyncio.gather(*tasks)

    if items:
        context: int = pagination.context + len(items)
        left: int = total - context
    else:
        context = 0
        left = 0

    return ResponseMultiPaginated[Cost](
        result=[Cost.model_validate(item) for item in items],
        context=context,
        left=left,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_cost(
    user: domain.users.User = Depends(op.authorize),
    body: CostCreateBody = Body(...),
) -> Response[Cost]:
    """add cost. side effect: the equity is decreased."""

    item: database.Cost = await op.add_cost(
        name=body.name,
        value=body.value,
        timestamp=body.timestamp,
        user_id=user.id,
        currency_id=body.currency_id,
        category_id=body.category_id,
    )

    return Response[Cost](result=Cost.model_validate(item))
