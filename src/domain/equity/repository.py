from typing import AsyncGenerator

from sqlalchemy import Result, select

from src.infrastructure import database

from .entities import Equity


class EquityRepository(database.Repository):
    async def currencies(self) -> tuple[database.Currency]:
        """select everything from 'currencies' table."""

        async with self.query.session as session:
            async with session.begin():
                result: Result = await session.execute(
                    select(database.Currency)
                )
                return tuple(result.scalars().all())

    async def add_currency(
        self, candidate: database.Currency
    ) -> database.Currency:
        """add item to the 'currencies' table."""

        self.command.session.add(candidate)
        return candidate

    async def decrease_equity(self, currency_id: int, total: int) -> Equity:
        """decrease the equity for a currency."""

        raise NotImplementedError

    async def increase_equity(self, currency_id: int, total: int) -> Equity:
        """increase the equity for a currency."""

        raise NotImplementedError
