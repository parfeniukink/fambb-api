from collections.abc import AsyncGenerator
from datetime import date

from src import domain


async def add_cost(
    user: domain.users.User, name: str, value: int, timestamp: date
):
    pass


async def get_transactions(
    currency_id: int | None,
) -> AsyncGenerator[domain.transactions.Transaction, None]:
    raise NotImplementedError


async def get_last_transactions() -> (
    AsyncGenerator[domain.transactions.Transaction, None]
):
    raise NotImplementedError
