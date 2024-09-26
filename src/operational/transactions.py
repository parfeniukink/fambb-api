from collections.abc import AsyncGenerator

from src.domain.transactions import Transaction, TransactionRepository


async def get_transactions(
    currency_id: int | None,
) -> AsyncGenerator[Transaction, None]:
    async for item in TransactionRepository().filter(
        operation=None, currency_id=currency_id
    ):
        yield item


async def get_last_transactions() -> AsyncGenerator[Transaction, None]:
    """Return all the transactions from the database,
    limited by user's settings.
    """

    limit = 10  # TODO: take this value form the database

    async for item in TransactionRepository().filter(
        operation=None, limit=limit
    ):
        yield item
