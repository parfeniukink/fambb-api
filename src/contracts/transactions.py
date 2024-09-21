import functools
from datetime import datetime

from pydantic import Field

from src import domain
from src.infrastructure import PublicData

from .currency import Currency


class Transaction(PublicData):
    """A public representation of any sort of a transaction in
    the system: cost, income, exchange.

    Notes:
        This class is mostly for the analytics.
    """

    operation: domain.transactions.OperationType
    name: str
    value: int
    currency: domain.finances.Currency

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Transaction":
        raise NotImplementedError(
            f"Can not convert {type(instance)} into the Equity contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.transactions.Transaction):
        return cls(
            operation=instance.operation,
            name=instance.name,
            value=instance.value,
            currency=domain.finances.Currency(
                id=instance.currency.id,
                name=instance.currency.name,
                sign=instance.currency.sign,
            ),
        )


class CostCategoryCreateBody(PublicData):
    """The request body to create a new cost category."""

    name: str


class CostCategory(CostCategoryCreateBody):
    """The public representation of a cost category."""

    id: int


class CostCreateBody(PublicData):
    """The request body to create a new cost."""

    name: str = Field(description="The name of the currency")
    value: int = Field(description="The value in cents")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency_id: int
    category_id: int


class Cost(PublicData):
    """The public representation of a cost."""

    id: int
    name: str
    value: int
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency: Currency
    category: CostCategory
