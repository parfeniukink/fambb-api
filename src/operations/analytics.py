from collections.abc import AsyncGenerator

from src import domain


async def get_transactions(
    currency_id: int | None,
) -> AsyncGenerator[domain.transactions.Transaction, None]:
    async for item in domain.transactions.TransactionRepository().filter(
        operation=None, currency_id=currency_id
    ):
        yield item


async def get_last_transactions() -> (
    AsyncGenerator[domain.transactions.Transaction, None]
):
    """Return all the transactions from the database,
    limited by user's settings.
    """

    limit = 10  # TODO: take this value form the database

    async for item in domain.transactions.TransactionRepository().filter(
        operation=None, limit=limit
    ):
        yield item
