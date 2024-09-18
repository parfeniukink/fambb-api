import random
from typing import AsyncGenerator

from .entities import CurrencyWithEquity


class CurrencyRepository:
    # TODO: Get real data
    async def all(self) -> AsyncGenerator[CurrencyWithEquity, None]:
        for item in [
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
        ]:
            yield item
