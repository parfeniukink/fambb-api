from src.infrastructure import InternalData


class CurrencyDBCandidate(InternalData):
    name: str
    sign: str


class Currency(CurrencyDBCandidate):
    """The currency representation which includes the equity information.

    Probably if you merge the equity concept with the currency it becomes
    the aggregate, but in that case the equity, on the domain level represents
    not the object-oriented structure, but the functional currency property.

    What it gives for us? So, each operation has a currency and we always have
    the access to the fresh equity data. In many places it allows you creating
    analytics very fast.
    """

    id: int


class CurrencyWithEquity(Currency):

    equity: int
