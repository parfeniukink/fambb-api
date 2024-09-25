"""
This is the Application (Operational) layer that could be treated
as a bridge between the Presentation layer and the rest of the application.

It basically represents all the operations in the whole application on
the top level.

Each component in this layer defines specific operations that are
allowed to be performed by the user of this system in general.
"""

__all__ = ("get_last_transactions", "get_transactions", "user_retrieve")

from collections.abc import AsyncGenerator

from src.domain.transactions import Transaction, TransactionRepository

from .users import user_retrieve


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
