from sqlalchemy import Result, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors


class Cash(database.DataAccessLayer):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session)

    async def cash_balances(self) -> list[database.CashBalance]:
        """Get all cash balances."""

        query: Select = (
            select(database.CashBalance)
            .options(
                joinedload(database.CashBalance.currency),
            )
            .order_by(database.CashBalance.id)
        )

        async with self._read_session() as session:
            results: Result = await session.execute(query)
            return list(results.scalars())

    async def cash_balance(self, id_: int) -> database.CashBalance:
        """Get a single cash balance by id."""

        async with self._read_session() as session:
            results: Result = await session.execute(
                select(database.CashBalance)
                .where(
                    database.CashBalance.id == id_,
                )
                .options(
                    joinedload(database.CashBalance.currency),
                )
            )
            if not (item := results.scalars().one_or_none()):
                raise errors.NotFoundError(f"Cash balance {id_} not found")

        return item

    async def add(
        self, candidate: database.CashBalance
    ) -> database.CashBalance:
        """Add a new cash balance record."""

        self._write_session.add(candidate)
        return candidate

    async def update(self, id_: int, **fields) -> None:
        """Update cash balance fields."""

        query = (
            update(database.CashBalance)
            .where(database.CashBalance.id == id_)
            .values(**fields)
        )

        await self._write_session.execute(query)

    async def delete_cash_balance(self, id_: int) -> None:
        """Delete a cash balance by id."""

        query = delete(database.CashBalance).where(
            database.CashBalance.id == id_
        )

        await self._write_session.execute(query)
