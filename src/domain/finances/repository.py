import random
from typing import AsyncGenerator

from .entities import CurrencyDBCandidate, CurrencyWithEquity


class FinancialRepository:
    _default_currencies = [
        CurrencyWithEquity(
            id=1,
            name="USD",
            sign="$",
            equity=random.randint(10000, 100000),
        ),
        CurrencyWithEquity(
            id=2,
            name="UAH",
            sign="#",
            equity=random.randint(10000, 100000),
        ),
    ]

    async def currencies(self) -> AsyncGenerator[CurrencyWithEquity, None]:
        """Select everything from 'currencies' table."""

        for item in self._default_currencies:
            yield item

    async def add_currency(
        self, candidate: CurrencyDBCandidate
    ) -> CurrencyWithEquity:
        """Add item to the 'currencies' table.

        Notes:
            If the ``name`` or the ``sign`` already exist in the table
            the error will be raised.
        """

        item = CurrencyWithEquity(
            id=FinancialRepository._default_currencies[-1].id + 1,
            name=candidate.name,
            sign=candidate.sign,
            equity=0,
        )

        FinancialRepository._default_currencies.append(item)

        return item
