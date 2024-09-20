import functools

from src import domain
from src.infrastructure import PublicData


class Equity(PublicData):
    currency: domain.finances.Currency
    amount: int

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Equity":
        raise NotImplementedError(
            f"Can not convert {type(instance)} into the Equity contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.finances.CurrencyWithEquity):
        return cls(
            currency=domain.finances.Currency(
                id=instance.id,
                name=instance.name,
                sign=instance.sign,
            ),
            amount=instance.equity,
        )



