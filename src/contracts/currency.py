import functools

from src import domain
from src.infrastructure.entities import PublicData


class CurrencyCreateBody(PublicData):
    """The request body to create a new currency."""

    name: str
    sign: str


class Currency(CurrencyCreateBody):
    """The public representation of a currency."""

    id: int

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Currency":
        raise NotImplementedError(
            f"Can not convert {type(instance)} into the Equity contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.finances.Currency):
        return cls(
            id=instance.id,
            name=instance.name,
            sign=instance.sign,
        )
