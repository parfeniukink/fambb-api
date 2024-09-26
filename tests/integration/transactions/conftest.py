import asyncio
from collections.abc import Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from src import domain
from src.infrastructure import database


class CostCandidateFactory(SQLAlchemyFactory[database.Cost]):
    __model__ = database.Cost


@pytest.fixture
async def cost_factory(
    john,
    currencies: list[database.Currency],
    cost_categories: list[database.CostCategory],
) -> Callable:
    """
    params:
        ``n`` - stands for number of generaget items.
    """

    currency = currencies[0]
    category = cost_categories[0]

    async def inner(n=1) -> list[database.Cost]:
        candidates = [
            CostCandidateFactory.build(
                user_id=john.id,
                currency_id=currency.id,
                category_id=category.id,
            )
            for _ in range(n)
        ]

        async with database.transaction() as session:
            tasks = [
                domain.transactions.TransactionRepository().add_cost(candidate)
                for candidate in candidates
            ]

            results: list[database.Cost] = await asyncio.gather(*tasks)
            await session.flush()

            return results

    return inner
