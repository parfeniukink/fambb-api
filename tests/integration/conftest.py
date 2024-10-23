import asyncio
import random
from collections.abc import Callable

import pytest
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from src import domain
from src.infrastructure import database


class CostCandidateFactory(SQLAlchemyFactory[database.Cost]):
    __model__ = database.Cost


class IncomeCandidateFactory(SQLAlchemyFactory[database.Income]):
    __model__ = database.Income


class ExchangeCandidateFactory(SQLAlchemyFactory[database.Exchange]):
    __model__ = database.Exchange


class CostShortcutCandidateFactory(SQLAlchemyFactory[database.CostShortcut]):
    __model__ = database.CostShortcut


@pytest.fixture
async def currencies() -> list[database.Currency]:
    """by default has 0 equity."""

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
        candidates = (
            CostCandidateFactory.build(
                user_id=john.id,
                currency_id=currency.id,
                category_id=category.id,
            )
            for _ in range(n)
        )

        async with database.transaction() as session:
            tasks = (
                domain.transactions.TransactionRepository().add_cost(candidate)
                for candidate in candidates
            )

            results: list[database.Cost] = await asyncio.gather(*tasks)
            await session.flush()

            return results

    return inner


@pytest.fixture
async def income_factory(
    john,
    currencies: list[database.Currency],
    source: domain.transactions.IncomeSource = "revenue",
) -> Callable:
    """
    params:
        ``n`` - stands for number of generaget items.
    """

    currency = currencies[0]

    async def inner(n=1) -> list[database.Income]:
        candidates = (
            IncomeCandidateFactory.build(
                user_id=john.id, currency_id=currency.id, source=source
            )
            for _ in range(n)
        )

        async with database.transaction() as session:
            tasks = (
                domain.transactions.TransactionRepository().add_income(
                    candidate
                )
                for candidate in candidates
            )

            results: list[database.Income] = await asyncio.gather(*tasks)
            await session.flush()

            return results

    return inner


@pytest.fixture
async def exchange_factory(
    john,
    currencies: list[database.Currency],
) -> Callable:
    """
    params:
        ``n`` - stands for number of generaget items.
    """

    from_currency, to_currency = currencies

    async def inner(n=1) -> list[database.Exchange]:
        candidates = (
            ExchangeCandidateFactory.build(
                user_id=john.id,
                from_currency_id=from_currency.id,
                to_currency_id=to_currency.id,
            )
            for _ in range(n)
        )

        async with database.transaction() as session:
            tasks = (
                domain.transactions.TransactionRepository().add_exchange(
                    candidate
                )
                for candidate in candidates
            )

            results: list[database.Exchange] = await asyncio.gather(*tasks)
            await session.flush()

            return results

    return inner


@pytest.fixture
async def cost_shortcut_factory(
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

    async def inner(
        n=1, value: int | None = None
    ) -> list[database.CostShortcut]:
        candidates = (
            CostShortcutCandidateFactory.build(
                user_id=john.id,
                currency_id=currency.id,
                category_id=category.id,
                value=value,
            )
            for _ in range(n)
        )

        async with database.transaction() as session:
            tasks = (
                domain.transactions.TransactionRepository().add_cost_shortcut(
                    candidate
                )
                for candidate in candidates
            )

            results: list[database.CostShortcut] = await asyncio.gather(*tasks)
            await session.flush()

            return results

    return inner
