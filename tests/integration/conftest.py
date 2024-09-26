import asyncio

import pytest

from src import domain
from src.infrastructure import database


@pytest.fixture
async def currencies() -> list[database.Currency]:
    async with database.transaction() as session:
        tasks = [
            domain.equity.EquityRepository().add_currency(
                database.Currency(name="USD", sign="$")
            ),
            domain.equity.EquityRepository().add_currency(
                database.Currency(name="FOO", sign="#")
            ),
        ]

        results = await asyncio.gather(*tasks)
        await session.flush()  # get ids

        return results


@pytest.fixture
async def cost_categories() -> list[database.CostCategory]:
    async with database.transaction() as session:
        tasks = [
            domain.transactions.TransactionRepository().add_cost_category(
                database.CostCategory(name="Food")
            ),
            domain.transactions.TransactionRepository().add_cost_category(
                database.CostCategory(name="Other")
            ),
        ]

        results = await asyncio.gather(*tasks)
        await session.flush()  # get ids

        return results
