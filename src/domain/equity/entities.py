import functools

from src.infrastructure import InternalData, database


class Currency(InternalData):
    """The currency representation which includes the equity information.

    Probably if you merge the equity concept with the currency it becomes
    the aggregate, but in that case the equity, on the domain level represents
    not the object-oriented structure, but the functional currency property.

    What it gives for us? So, each operation has a currency and we always have
    the access to the fresh equity data. In many places it allows you creating
    analytics very fast.
    """

    id: int
    name: str
    sign: str

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Currency":
        raise NotImplementedError(
            f"Can not get {cls.__name__} from {type(instance)} type"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.Currency):
        return cls(
            id=instance.id,
            name=instance.name,
            sign=instance.sign,
        )


class Equity(Currency):

    equity: int
