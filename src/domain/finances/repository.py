from typing import AsyncGenerator

from tests.mock_storage import Storage

from .entities import CurrencyDBCandidate, CurrencyWithEquity


class FinancialRepository:
    async def currencies(self) -> AsyncGenerator[CurrencyWithEquity, None]:
        """Select everything from 'currencies' table."""

        for item in Storage.currencies.values():
            yield CurrencyWithEquity(**item)

    async def add_currency(
        self, candidate: CurrencyDBCandidate
    ) -> CurrencyWithEquity:
        """Add item to the 'currencies' table.

        Notes:
            If the ``name`` or the ``sign`` already exist in the table
            the error will be raised.
        """

        new_id: int = max(Storage.currencies.keys()) + 1
        instance: dict = dict(
            id=new_id,
            name=candidate.name,
            sign=candidate.sign,
            equity=0,
        )
        Storage.currencies[new_id] = instance

        return CurrencyWithEquity(**instance)
