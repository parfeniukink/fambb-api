from collections.abc import AsyncGenerator
from datetime import date

from src import domain
from src.infrastructure import database


async def add_cost(
    name: str,
    value: int,
    timestamp: date,
    currency_id: int,
    category_id: int,
    user_id: int,
) -> database.Cost:
    async with database.transaction():
        instance = await domain.transactions.TransactionRepository().add_cost(
            candidate=database.Cost(
                name=name,
                value=value,
                timestamp=timestamp,
                user_id=user_id,
                currency_id=currency_id,
                category_id=category_id,
            )
        )

        # TODO: decrease the equity

    return await domain.transactions.TransactionRepository().cost(
        id_=instance.id
    )


async def get_costs(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Cost, ...]:
    """get paginated costs. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().costs(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def get_transactions(
    currency_id: int | None,
) -> AsyncGenerator[domain.transactions.Transaction, None]:
    raise NotImplementedError
    yield


async def get_last_transactions() -> (
    AsyncGenerator[domain.transactions.Transaction, None]
):
    raise NotImplementedError
    yield
