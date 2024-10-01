import asyncio
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

    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_cost(
                candidate=database.Cost(
                    name=name,
                    value=value,
                    timestamp=timestamp,
                    user_id=user_id,
                    currency_id=currency_id,
                    category_id=category_id,
                )
            ),
            domain.equity.EquityRepository().decrease_equity(
                currency_id, value
            ),
        )
        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

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


async def get_incomes(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Income, ...]:
    """get paginated incomes. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().incomes(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def add_income(
    name: str,
    value: int,
    timestamp: date,
    source: domain.transactions.IncomeSource,
    currency_id: int,
    user_id: int,
) -> database.Income:
    """add another yet income and change the currency equity."""

    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_income(
                candidate=database.Income(
                    name=name,
                    value=value,
                    timestamp=timestamp,
                    source=source,
                    currency_id=currency_id,
                    user_id=user_id,
                )
            ),
            domain.equity.EquityRepository().increase_equity(
                currency_id, value
            ),
        )
        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

    return await domain.transactions.TransactionRepository().income(
        id_=instance.id
    )


async def get_currency_exchanges(
    limit: int,
    offset: int,
    user_id: int | None = None,
) -> tuple[database.Exchange, ...]:
    """get paginated costs. proxy values to the repository."""

    items = tuple(
        [
            item
            async for item in domain.transactions.TransactionRepository().exchanges(
                user_id=user_id, offset=offset, limit=limit
            )
        ]
    )

    return items


async def currency_exchange(
    from_value: int,
    to_value: int,
    timestamp: date,
    from_currency_id: int,
    to_currency_id: int,
    user_id: int,
) -> database.Exchange:
    async with database.transaction() as session:
        tasks = (
            domain.transactions.TransactionRepository().add_exchange(
                candidate=database.Exchange(
                    to_value=from_value,
                    from_value=to_value,
                    timestamp=timestamp,
                    from_currency_id=from_currency_id,
                    to_currency_id=to_currency_id,
                    user_id=user_id,
                )
            ),
            domain.equity.EquityRepository().decrease_equity(
                currency_id=from_currency_id, value=from_value
            ),
            domain.equity.EquityRepository().increase_equity(
                currency_id=to_currency_id, value=to_value
            ),
        )

        instance, *_ = await asyncio.gather(*tasks)
        await session.flush()

    return await domain.transactions.TransactionRepository().exchange(
        id_=instance.id
    )


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
