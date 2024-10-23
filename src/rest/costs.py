import asyncio

from fastapi import APIRouter, Body, Depends, status

from src import domain
from src import operational as op
from src.contracts import (
    Cost,
    CostCategory,
    CostCategoryCreateBody,
    CostCreateBody,
    CostShortcut,
    CostShortcutApply,
    CostShortcutCreateBody,
    CostUpdateBody,
)
from src.infrastructure import (
    OffsetPagination,
    Response,
    ResponseMulti,
    ResponseMultiPaginated,
    database,
    get_offset_pagination_params,
)

router = APIRouter(prefix="/costs", tags=["Transactions", "Costs"])


# ===========================================================
# cost categories section.
# on top because of the FastAPI router dispatching hierarchy
# ===========================================================
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


# ===========================================================
# cost shortcuts section.
# on top because of the FastAPI router dispatching hierarchy
# ===========================================================
@router.post(
    "/shortcuts",
    status_code=status.HTTP_201_CREATED,
    tags=["Transactions", "Shortcuts"],
)
async def cost_shortcut_create(
    user: domain.users.User = Depends(op.authorize),
    body: CostShortcutCreateBody = Body(...),
) -> Response[CostShortcut]:
    """Create yet another 'Cost Shortcut'."""

    payload = body.model_dump(exclude_unset=True) | {
        "user": user,
        "value": body.value_in_cents,
    }
    item: database.CostShortcut = await op.add_cost_shortcut(**payload)

    return Response[CostShortcut](result=CostShortcut.from_instance(item))


@router.get("/shortcuts", tags=["Transactions", "Shortcuts"])
async def cost_shortcuts(
    user: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[CostShortcut]:
    """Create yet another 'Cost Shortcut'."""

    return ResponseMulti[CostShortcut](
        result=[
            CostShortcut.from_instance(item)
            for item in await op.get_cost_shortcuts(user)
        ]
    )


@router.delete(
    "/shortcuts/{shortcut_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Transactions", "Shortcuts"],
)
async def cost_shortcut_delete(
    shortcut_id: int, user: domain.users.User = Depends(op.authorize)
) -> None:
    """delete the existing eost shortcut."""

    await op.delete_cost_shortcut(user, shortcut_id)


@router.post(
    "/shortcuts/{shortcut_id}",
    status_code=status.HTTP_201_CREATED,
    tags=["Transactions", "Shortcuts"],
)
async def cost_shortcut_apply(
    shortcut_id: int,
    user: domain.users.User = Depends(op.authorize),
    body: CostShortcutApply | None = Body(default=None),
) -> Response[Cost]:
    """delete the existing eost shortcut."""

    cost: database.Cost = await op.apply_cost_shortcut(
        user,
        shortcut_id,
        value=domain.transactions.cents_from_raw(body.value) if body else None,
    )

    return Response[Cost](result=Cost.from_instance(cost))


# ===========================================================
# cost section
# ===========================================================
@router.get("", status_code=status.HTTP_200_OK)
async def costs(
    user: domain.users.User = Depends(op.authorize),
    pagination: OffsetPagination = Depends(get_offset_pagination_params),
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
        result=[Cost.from_instance(item) for item in items],
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
        value=body.value_in_cents,
        timestamp=body.timestamp,
        user_id=user.id,
        currency_id=body.currency_id,
        category_id=body.category_id,
    )

    return Response[Cost](result=Cost.from_instance(item))


@router.get("/{cost_id}", status_code=status.HTTP_200_OK)
async def get_cost(
    cost_id: int, _: domain.users.User = Depends(op.authorize)
) -> Response[Cost]:
    """get an existing cost."""

    async with database.transaction():
        cost: database.Cost = (
            await domain.transactions.TransactionRepository().cost(id_=cost_id)
        )

    return Response[Cost](result=Cost.from_instance(cost))


@router.patch("/{cost_id}", status_code=status.HTTP_200_OK)
async def update_cost(
    cost_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: CostUpdateBody = Body(...),
) -> Response[Cost]:
    """add cost. side effect: the equity is decreased."""

    payload = body.model_dump(exclude_unset=True)
    if _value := body.value_in_cents:
        payload |= {"value": _value}

    item: database.Cost = await op.update_cost(cost_id=cost_id, **payload)

    return Response[Cost](result=Cost.from_instance(item))


@router.delete("/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost(
    cost_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """delete cost. side effect: the equity is decreased."""

    await op.delete_cost(cost_id=cost_id)
