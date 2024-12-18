import asyncio
import itertools
import operator
from collections.abc import AsyncGenerator
from datetime import date

from sqlalchemy import (
    Result,
    Select,
    String,
    delete,
    desc,
    func,
    select,
    union_all,
    update,
)
from sqlalchemy.orm import aliased, joinedload

from src.domain.equity import Currency
from src.infrastructure import database, errors

from .entities import CostCategory
from .value_objects import (
    CostsByCategory,
    IncomesBySource,
    Transaction,
    TransactionsBasicAnalytics,
)


class TransactionRepository(database.Repository):
    """
    ``TransactionRepository`` is a data access entrypoint.
    it allows manage costs, incomes, exchanges.

    it uses the 'Query Builder' to create SQL queries.
    """

    # ==================================================
    # unified || aggregated section
    # ==================================================
    async def transactions(
        self, /, currency_id: int | None, **kwargs
    ) -> tuple[tuple[Transaction, ...], int]:
        """get all the items from 'costs', 'incomes', 'exchanges' tables
        in the internal representation.
        """

        CurrencyAlias = aliased(database.Currency)
        UserAlias = aliased(database.User)

        # select costs
        cost_query = (
            select(
                database.Cost.id.label("id"),
                database.Cost.name.label("name"),
                database.Cost.value.label("value"),
                database.Cost.timestamp.label("timestamp"),
                func.cast("cost", String).label(  # type: ignore[arg-type]
                    "operation_type",
                ),
                CurrencyAlias,
                UserAlias.name,
            )
            .join(CurrencyAlias, database.Cost.currency)
            .join(UserAlias, database.Cost.user)
        )

        # select incomes
        income_query = (
            select(
                database.Income.id.label("id"),
                database.Income.name.label("name"),
                database.Income.value.label("value"),
                database.Income.timestamp.label("timestamp"),
                func.cast("income", String).label(  # type: ignore[arg-type]
                    "operation_type",
                ),
                CurrencyAlias,
                UserAlias.name,
            )
            .join(CurrencyAlias, database.Income.currency)
            .join(UserAlias, database.Income.user)
        )

        # select exchanges
        exchange_query = (
            select(
                database.Exchange.id.label("id"),
                func.cast("exchange", String).label(  # type: ignore[arg-type]
                    "name",
                ),
                database.Exchange.to_value.label("value"),
                database.Exchange.timestamp.label("timestamp"),
                func.cast("exchange", String).label(  # type: ignore[arg-type]
                    "operation_type",
                ),
                CurrencyAlias,
                UserAlias.name,
            )
            .join(CurrencyAlias, database.Exchange.to_currency)
            .join(UserAlias, database.Exchange.user)
        )

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
        union_query = (
            union_all(cost_query, income_query, exchange_query)
            .order_by(desc("timestamp"))
            .order_by(desc("id"))
        )

        paginated_query = self._add_pagination_filters(union_query, **kwargs)
        count_query = select(func.count()).select_from(
            union_query,  # type: ignore[arg-type]
        )

        results: list[Transaction] = []

        # execute the query and map results to ``Transaction`` attributes
        async with self.query.session as session:
            async with session.begin():
                # calculate total
                count_result = await session.execute(count_query)
                if (total := count_result.scalar()) is None:
                    raise errors.DatabaseError("Can't get the total of items")

                result = await session.execute(paginated_query)
                for row in result:
                    (
                        id_,
                        name,
                        value,
                        timestamp,
                        operation_type,
                        currency_name,
                        currency_sign,
                        _,  # currency equity
                        _currency_id,
                        user_name,
                    ) = row

                    results.append(
                        Transaction(
                            id=id_,
                            name=name,
                            value=value,
                            timestamp=timestamp,
                            operation=operation_type,
                            currency=Currency(
                                id=_currency_id,
                                name=currency_name,
                                sign=currency_sign,
                            ),
                            user=user_name,
                        )
                    )

        return tuple(results), total

    async def delete(self, table, candidate_id) -> None:
        """delete some specific trasaction from the specified table."""

        query = delete(table).where(getattr(table, "id") == candidate_id)
        await self.command.session.execute(query)

    # ==================================================
    # costs section
    # ==================================================
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
                joinedload(database.Cost.user),
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
                        joinedload(database.Cost.user),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Cost {id_} not found")
        return item

    async def add_cost(self, candidate: database.Cost) -> database.Cost:
        """add item to the 'costs' table."""

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

    # ==================================================
    # incomes section
    # ==================================================
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
                joinedload(database.Income.user),
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
                        joinedload(database.Income.user),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Income {id_} not found")
        return item

    async def add_income(self, candidate: database.Income) -> database.Income:
        """add item to the 'incomes' table."""

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

    # ==================================================
    # exchanges section
    # ==================================================
    async def exchanges(
        self, /, **kwargs
    ) -> AsyncGenerator[database.Exchange, None]:
        """get all exchanges from 'exchanges' table"""

        query: Select = (
            select(database.Exchange)
            .options(
                joinedload(database.Exchange.from_currency),
                joinedload(database.Exchange.to_currency),
                joinedload(database.Exchange.user),
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
                        joinedload(database.Exchange.user),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(f"Exchange {id_} not found")

        return item

    async def add_exchange(
        self, candidate: database.Exchange
    ) -> database.Exchange:
        """add item to the 'exchanges' table."""

        self.command.session.add(candidate)
        return candidate

    # ==================================================
    # cost shortcuts section
    # ==================================================
    async def cost_shortcuts(
        self, user_id: int
    ) -> AsyncGenerator[database.CostShortcut, None]:
        """return all the cost shortcuts from the  database."""

        query: Select = (
            select(database.CostShortcut)
            .where(database.CostShortcut.user_id == user_id)
            .options(
                joinedload(database.CostShortcut.currency),
                joinedload(database.CostShortcut.category),
            )
            .order_by(database.CostShortcut.id)
        )

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(query)
                for item in results.scalars():
                    yield item

    async def add_cost_shortcut(
        self, candidate: database.CostShortcut
    ) -> database.CostShortcut:
        """add item to the 'cost_shortcuts' table."""

        self.command.session.add(candidate)
        return candidate

    async def cost_shortcut(
        self, user_id: int, id_: int
    ) -> database.CostShortcut:
        """get specific item from 'cost_shortcuts' table."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.CostShortcut)
                    .where(
                        database.CostShortcut.id == id_,
                        database.CostShortcut.user_id == user_id,
                    )
                    .options(
                        joinedload(database.CostShortcut.currency),
                        joinedload(database.CostShortcut.category),
                    )
                )
                if not (item := results.scalars().one_or_none()):
                    raise errors.NotFoundError(
                        f"Cost Shortcut {id_} not found"
                    )

        return item

    # ==================================================
    # analytics section
    # ==================================================
    async def transactions_basic_analytics(
        self, /, start_date: date, end_date: date
    ) -> tuple[TransactionsBasicAnalytics, ...]:
        """build the transactions 'basic analytics' on the database level.

        args:
            ``currency_id`` - ID of the currency to filter by, if specified.
            ``start_date`` - Starting date of the analytics period.
            ``end_date`` - Ending date of the analytics period.


        workflow:
            build database queries. all (except of exchanges)
                are grouped by currency
            execute SQL queries asynchronously
            build the internal data structure to be returned

        notes:
            the 'key' of the result dictionary belongs
            to the `currency_id` of the related analytics block.
        """

        # ==================================================
        # costs section
        # ==================================================
        cost_totals_by_currency_query: Select = (
            select(
                database.Cost.currency_id.label("currency_id"),
                func.sum(database.Cost.value).label("total"),
            )
            .where(
                database.Cost.timestamp.between(start_date, end_date),
            )
            .group_by(database.Cost.currency_id)
            .order_by(database.Cost.currency_id)
        )

        cost_categories_totals_by_currency_query: Select = (
            select(
                # cost && cost category
                database.Cost.currency_id.label("currency_id"),
                database.CostCategory.name.label("category_name"),
                # custom calculation. the `sum` of all the costs in the range
                (func.sum(database.Cost.value)).label("total"),
            )
            .join(
                database.CostCategory,
                database.Cost.category_id == database.CostCategory.id,
            )
            .where(
                database.Cost.timestamp.between(start_date, end_date),
            )
            .group_by(database.Cost.currency_id, database.CostCategory.id)
            .order_by(database.Cost.currency_id, database.CostCategory.id)
        )

        # ==================================================
        # incomes section
        # ==================================================
        income_totals_by_currency_query: Select = (
            select(
                database.Income.currency_id.label("currency_id"),
                func.sum(database.Income.value).label("total"),
            )
            .where(
                database.Income.timestamp.between(start_date, end_date),
            )
            .group_by(database.Income.currency_id)
            .order_by(database.Income.currency_id)
        )

        incomes_by_currency_and_source_query: Select = (
            select(
                # income
                database.Income.currency_id.label("currency_id"),
                database.Income.source.label("source"),
                # custom calculation. the `sum` of all the incomes in the range
                (func.sum(database.Income.value)).label("total"),
            )
            .where(
                database.Income.timestamp.between(start_date, end_date),
            )
            .group_by(database.Income.currency_id, database.Income.source)
            .order_by(database.Income.currency_id, database.Income.source)
        )

        exchanges_query: Select = (
            select(database.Exchange)
            .where(
                database.Exchange.timestamp.between(start_date, end_date),
            )
            .order_by(database.Exchange.timestamp)
        )

        # perform database queries
        async with self.query.session as session:
            async with session.begin():
                try:
                    (
                        _currencies,
                        _costs_totals_by_currency,
                        _cost_totals_by_currency_and_category,
                        _incomes_totals_by_currency,
                        _income_totals_by_currency_and_source,
                        _exchanges,
                    ) = await asyncio.gather(
                        session.execute(
                            select(database.Currency).order_by(
                                desc(database.Currency.id)
                            )
                        ),
                        session.execute(cost_totals_by_currency_query),
                        session.execute(
                            cost_categories_totals_by_currency_query
                        ),
                        session.execute(income_totals_by_currency_query),
                        session.execute(incomes_by_currency_and_source_query),
                        session.execute(exchanges_query),
                    )

                except Exception as error:
                    raise errors.DatabaseError(str(error)) from error

        results: dict[int, TransactionsBasicAnalytics] = {
            currency.id: TransactionsBasicAnalytics(
                currency=Currency.from_instance(currency)
            )
            for currency in _currencies.scalars().all()
        }

        # update costs currency total
        for currency_id, total in _costs_totals_by_currency:
            results[currency_id].costs.total = total

        # update incomes currency total
        for currency_id, total in _incomes_totals_by_currency:
            results[currency_id].incomes.total = total

        # update cost categories totals
        for currency_id, items in itertools.groupby(
            _cost_totals_by_currency_and_category,
            key=operator.attrgetter("currency_id"),
        ):
            results[currency_id].costs.by_category += [
                CostsByCategory(
                    name=category_name,
                    total=total,
                    ratio=total / results[currency_id].costs.total * 100,
                )
                for _, category_name, total in items
            ]

        # update incomes sources totals
        for currency_id, items in itertools.groupby(
            _income_totals_by_currency_and_source,
            key=operator.attrgetter("currency_id"),
        ):
            results[currency_id].incomes.by_source += [
                (IncomesBySource(source=source, total=total))
                for _, source, total in items
            ]

        for item in _exchanges.scalars().all():
            results[item.from_currency_id].from_exchanges -= item.from_value
            results[item.to_currency_id].from_exchanges += item.to_value

        return tuple(results.values())
