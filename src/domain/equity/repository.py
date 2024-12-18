from sqlalchemy import Result, desc, select, update

from src.infrastructure import database


class EquityRepository(database.Repository):
    async def currency(self, id_: int) -> database.Currency:
        """search by ``id``."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.Currency).where(
                        database.Currency.id == id_
                    )
                )
                item: database.Currency = results.scalars().one()

        return item

    async def currencies(self) -> tuple[database.Currency, ...]:
        """select everything from 'currencies' table."""

        async with self.query.session as session:
            async with session.begin():
                result: Result = await session.execute(
                    select(database.Currency).order_by(
                        desc(database.Currency.id)
                    )
                )

        return tuple(result.scalars().all())

    async def add_currency(
        self, candidate: database.Currency
    ) -> database.Currency:
        """add item to the 'currencies' table."""

        self.command.session.add(candidate)
        return candidate

    async def decrease_equity(self, currency_id: int, value: int) -> None:
        """decrease the equity for a currency."""

        query = (
            update(database.Currency)
            .where(database.Currency.id == currency_id)
            .values({"equity": database.Currency.equity - value})
            .returning(database.Currency)
        )

        await self.command.session.execute(query)

    async def increase_equity(self, currency_id: int, value: int) -> None:
        """increase the equity for a currency."""

        query = (
            update(database.Currency)
            .where(database.Currency.id == currency_id)
            .values({"equity": database.Currency.equity + value})
            .returning(database.Currency)
        )

        await self.command.session.execute(query)
