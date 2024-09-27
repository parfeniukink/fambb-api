import itertools
import operator
from collections.abc import AsyncGenerator

from sqlalchemy import Result, select

from src.infrastructure import database
from tests.mock_storage import Storage

from ..equity import Currency
from .entities import (
    Cost,
    CostCategory,
    Exchange,
    Income,
    OperationType,
    Transaction,
)


class TransactionRepository(database.Repository):
    """
    TransactionRepository is a data access entrypoint.
    It allows manage costs, incomes, exchanges.
    Everything that could be treated as a 'Money Transaction'.

    It uses the 'Query Builder' to create SQL queries.
    """

    async def transactions(
        self, batch_size: int | None = None
    ) -> AsyncGenerator[Transaction, None]:
        """get all the items from 'costs', 'incomes', 'exchanges' tables
        in the internal representation.

        params:
            ``batch_size`` configures how the data is going to be fetched
                           from the database. if `None` - regular fetch all
                           items from the database.
        """

        raise NotImplementedError

    async def cost_categories(self) -> AsyncGenerator[CostCategory, None]:
        """get all items from 'cost_categories' table"""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.CostCategory)
                )
                for item in results.scalars():
                    yield item

    async def add_cost_category(
        self, candidate: database.CostCategory
    ) -> database.CostCategory:
        """add item to the 'cost_categories' table."""

        self.command.session.add(candidate)
        return candidate

    async def add_cost(self, candidate: database.Cost) -> database.Cost:
        """Add item to the 'costs' table."""

        self.command.session.add(candidate)
        return candidate

    async def add_income(self, candidate: database.Income) -> database.Income:
        """Add item to the 'incomes' table."""

        self.command.session.add(candidate)
        return candidate

    async def add_exchange(
        self, candidate: database.Exchange
    ) -> database.Exchange:
        """Add item to the 'exchanges' table."""

        self.command.session.add(candidate)
        return candidate
