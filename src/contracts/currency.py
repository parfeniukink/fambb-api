import functools

from pydantic import Field

from src.infrastructure import PublicData, database


class CurrencyCreateBody(PublicData):
    """The request body to create a new currency."""

    name: str = Field(description="International name of a currency")
    sign: str = Field(description="International sign of a currency")


class Currency(CurrencyCreateBody):
    """The public representation of a currency."""

    id: int = Field(description="Unique identifier in the system")

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Currency":
        raise NotImplementedError(
            f"Can not convert {type(instance)} into the Equity contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.Currency):
        return cls(
            id=instance.id,
            name=instance.name,
            sign=instance.sign,
        )
