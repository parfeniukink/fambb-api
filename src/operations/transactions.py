from src.domain.transactions import (
    Cost,
    CostCateogoryFlat,
    CostFlat,
    TransactionRepository,
)


async def cost_category_create(name: str) -> CostCateogoryFlat:
    """Create a new cost category if the name does not exist."""

    return await TransactionRepository().add_cost_category(name=name)
