from collections.abc import AsyncGenerator

from sqlalchemy import (
    Result,
    Select,
    String,
    delete,
    func,
    select,
    union_all,
    update,
)
from sqlalchemy.orm import aliased, joinedload

from src import domain
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
        self, /, currency_id: int | None, **kwargs
    ) -> tuple[tuple[Transaction, ...], int]:
        """get all the items from 'costs', 'incomes', 'exchanges' tables
        in the internal representation.
        """

        CurrencyAlias = aliased(database.Currency)

        # select costs
        cost_query = select(
            database.Cost.name.label("name"),
            database.Cost.value.label("value"),
            database.Cost.timestamp.label("timestamp"),
            func.cast("cost", String).label("operation_type"),  # type: ignore[arg-type]
            CurrencyAlias,
        ).join(CurrencyAlias, database.Cost.currency)

        # select incomes
        income_query = select(
            database.Income.name.label("name"),
            database.Income.value.label("value"),
            database.Income.timestamp.label("timestamp"),
            func.cast("income", String).label("operation_type"),  # type: ignore[arg-type]
            CurrencyAlias,
        ).join(CurrencyAlias, database.Income.currency)

        # select exchanges
        exchange_query = select(
            func.cast("exchange", String).label("name"),  # type: ignore[arg-type]
            database.Exchange.to_value.label("value"),
            database.Exchange.timestamp.label("timestamp"),
            func.cast("exchange", String).label("operation_type"),  # type: ignore[arg-type]
            CurrencyAlias,
        ).join(CurrencyAlias, database.Exchange.to_currency)

        # add currency filter if specified
        if currency_id is not None:
            cost_query = cost_query.where(
                database.Cost.currency_id == currency_id
            )
            income_query = income_query.where(
                database.Income.currency_id == currency_id
            )
            exchange_query = exchange_query.where(
                database.Exchange.to_currency_id == currency_id
            )

        # combine all the queries using UNION ALL
        union_query = union_all(
            cost_query, income_query, exchange_query
        ).order_by("timestamp")

        paginated_query = self._add_pagination_filters(union_query, **kwargs)
        count_query = select(func.count()).select_from(union_query)  # type: ignore[arg-type]

        results: list[Transaction] = []

        # execute the query and map results to ``Transaction`` attributes
        async with self.query.session as session:
            async with session.begin():
                # calculate total
                count_result = await session.execute(count_query)
                if not (total := count_result.scalar()):
                    raise errors.DatabaseError("Can't get the total of items")

                result = await session.execute(paginated_query)
                for row in result:
                    (
                        name,
                        value,
                        timestamp,
                        operation_type,
                        currency_name,
                        currency_sign,
                        _,  # currency equity
                        _currency_id,
                    ) = row

                    results.append(
                        Transaction(
                            name=name,
                            value=value,
                            timestamp=timestamp,
                            operation=operation_type,
                            currency=domain.equity.Currency(
                                id=_currency_id,
                                name=currency_name,
                                sign=currency_sign,
                            ),
                        )
                    )

        return tuple(results), total

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

    async def update_income(
        self, candidate: database.Income, **values
    ) -> database.Income:

        query = (
            update(database.Income)
            .where(database.Income.id == candidate.id)
            .values(values)
            .returning(database.Income)
        )

        await self.command.session.execute(query)

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
        """add item to the 'exchanges' table."""

        self.command.session.add(candidate)
        return candidate

    async def delete(self, table, candidate_id) -> None:
        """delete some specific trasaction from the database."""

        query = delete(table).where(getattr(table, "id") == candidate_id)
        await self.command.session.execute(query)
