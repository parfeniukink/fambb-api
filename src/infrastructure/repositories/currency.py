from sqlalchemy import Result, desc, exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure import database, errors


class Currency(database.DataAccessLayer):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session)

    async def currency(self, id_: int) -> database.Currency:
        """search by ``id``."""

        async with self._read_session() as session:
            results: Result = await session.execute(
                select(database.Currency).where(database.Currency.id == id_)
            )
            item: database.Currency = results.scalars().one()

        return item

    async def currencies(
        self,
    ) -> tuple[database.Currency, ...]:
        """select everything from 'currencies' table."""

        async with self._read_session() as session:
            result: Result = await session.execute(
                select(database.Currency).order_by(desc(database.Currency.id))
            )

        return tuple(result.scalars().all())

    async def add_currency(
        self, candidate: database.Currency
    ) -> database.Currency:
        """add item to the 'currencies' table."""

        self._write_session.add(candidate)
        return candidate

    async def delete_currency(self, currency_id: int) -> None:
        """delete currency if not related to any transactions."""

        query = select(
            or_(
                exists().where(database.Cost.currency_id == currency_id),
                exists().where(database.Income.currency_id == currency_id),
                exists().where(
                    database.Exchange.from_currency_id == currency_id
                ),
                exists().where(
                    database.Exchange.to_currency_id == currency_id
                ),
            )
        )

        async with self._read_session() as session:
            result = await session.execute(query)
            currency_used: bool = result.scalar_one()

        if currency_used is True:
            raise errors.BadRequestError(
                message="You can't remove currencies that are in use"
            )
        else:
            await self.delete(database.Currency, candidate_id=currency_id)

    async def decrease_equity(self, currency_id: int, value: int) -> None:
        """decrease the equity for a currency."""

        query = (
            update(database.Currency)
            .where(database.Currency.id == currency_id)
            .values({"equity": database.Currency.equity - value})
            .returning(database.Currency)
        )

        await self._write_session.execute(query)

    async def increase_equity(self, currency_id: int, value: int) -> None:
        """increase the equity for a currency."""

        query = (
            update(database.Currency)
            .where(database.Currency.id == currency_id)
            .values({"equity": database.Currency.equity + value})
            .returning(database.Currency)
        )

        await self._write_session.execute(query)
