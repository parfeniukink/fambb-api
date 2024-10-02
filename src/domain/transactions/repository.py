from collections.abc import AsyncGenerator

from sqlalchemy import Result, Select, select, update
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors

from .entities import CostCategory, Transaction


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

    async def costs(self, /, **kwargs) -> AsyncGenerator[database.Cost, None]:
        """get all items from 'costs' table.

        notes:
            kwargs are passed to the self._add_pagination_filters()
        """

        query: Select = (
            select(database.Cost)
            .options(
                joinedload(database.Cost.currency),
                joinedload(database.Cost.category),
            )
            .order_by(database.Cost.timestamp)
        )

        query = self._add_pagination_filters(query, **kwargs)

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(query)
                for item in results.scalars():
                    yield item

    async def cost(self, id_: int) -> database.Cost:
        """get specific item from 'costs' table"""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.Cost)
                    .where(database.Cost.id == id_)
                    .options(
                        joinedload(database.Cost.currency),
                        joinedload(database.Cost.category),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Cost {id_} not found")
                else:
                    return item

    async def add_cost(self, candidate: database.Cost) -> database.Cost:
        """Add item to the 'costs' table."""

        self.command.session.add(candidate)
        return candidate

    async def update_cost(
        self, candidate: database.Cost, **values
    ) -> database.Cost:

        query = (
            update(database.Cost)
            .where(database.Cost.id == candidate.id)
            .values(values)
            .returning(database.Cost)
        )

        await self.command.session.execute(query)

        return candidate

    async def incomes(
        self, /, **kwargs
    ) -> AsyncGenerator[database.Income, None]:
        """get all incomes from 'incomes' table

        notes:
            kwargs are passed to the self._add_pagination_filters()
        """

        query: Select = (
            select(database.Income)
            .options(
                joinedload(database.Income.currency),
            )
            .order_by(database.Income.timestamp)
        )

        query = self._add_pagination_filters(query, **kwargs)

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(query)
                for item in results.scalars():
                    yield item

    async def income(self, id_: int) -> database.Income:
        """get specific item from 'incomes' table"""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.Income)
                    .where(database.Income.id == id_)
                    .options(
                        joinedload(database.Income.currency),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Income {id_} not found")
                else:
                    return item

    async def add_income(self, candidate: database.Income) -> database.Income:
        """Add item to the 'incomes' table."""

        self.command.session.add(candidate)
        return candidate

    async def exchanges(
        self, /, **kwargs
    ) -> AsyncGenerator[database.Exchange, None]:
        """get all exchanges from 'exchanges' table"""

        query: Select = (
            select(database.Exchange)
            .options(
                joinedload(database.Exchange.from_currency),
                joinedload(database.Exchange.to_currency),
            )
            .order_by(database.Exchange.timestamp)
        )

        query = self._add_pagination_filters(query, **kwargs)

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(query)
                for item in results.scalars():
                    yield item

    async def exchange(self, id_: int) -> database.Exchange:
        """get specific item from 'exchange' table"""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.Exchange)
                    .where(database.Exchange.id == id_)
                    .options(
                        joinedload(database.Exchange.from_currency),
                        joinedload(database.Exchange.to_currency),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Exchange {id_} not found")
                else:
                    return item

    async def add_exchange(
        self, candidate: database.Exchange
    ) -> database.Exchange:
        """Add item to the 'exchanges' table."""

        self.command.session.add(candidate)
        return candidate
