import functools
from datetime import date

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

    operation: domain.transactions.OperationType = Field(
        description="The type of the operation"
    )
    name: str = Field(description="The name of the transaction")
    value: int = Field(description="The value in cents")
    timestamp: date = Field(
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency: str = Field(description="The sign of the currency")

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
            timestamp=instance.timestamp,
            currency=instance.currency.sign,
        )


class CostCategoryCreateBody(PublicData):
    """The request body to create a new cost category."""

    name: str


class CostCategory(CostCategoryCreateBody):
    """The public representation of a cost category."""

    id: int


class CostCreateBody(PublicData):
    """The request body to create a new cost."""

    name: str = Field(description="The name of the cost")
    value: int = Field(description="The value in cents")
    timestamp: date = Field(
        default_factory=date.today,
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency_id: int
    category_id: int


class CostUpdateBody(PublicData):
    """The request body to update the existing cost."""

    name: str | None = Field(
        default=None,
        description="The name of the currency",
    )
    value: int | None = Field(default=None, description="The value in cents")
    timestamp: date | None = Field(
        default=None,
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency_id: int | None = Field(
        default=None,
        description="A new currency id. Must be different from the previous one",
    )
    category_id: int | None = Field(
        default=None,
        description="A new currency id. Must be different from the previous one",
    )


class Cost(PublicData):
    """The public representation of a cost."""

    id: int
    name: str
    value: int
    timestamp: date
    currency: Currency
    category: CostCategory


class IncomeCreateBody(PublicData):
    """The request body to create a new income."""

    name: str = Field(description="The name of the income")
    value: int = Field(description="The value in cents")
    source: domain.transactions.IncomeSource = Field(
        default="revenue", description="Available 'source' for the income."
    )
    timestamp: date = Field(
        default_factory=date.today,
        description=("The date of a transaction"),
    )
    currency_id: int = Field(description="Internal currency system identifier")


class IncomeUpdateBody(PublicData):
    """The request body to update the existing income."""

    name: str | None = Field(
        default=None,
        description="The name of the income",
    )
    value: int | None = Field(default=None, description="The value in cents")
    source: domain.transactions.IncomeSource | None = Field(
        default=None,
        description="The income source",
    )
    timestamp: date | None = Field(
        default=None,
        description=(
            "Define the timestamp for the cost. The default value is 'now'"
        ),
    )
    currency_id: int | None = Field(
        default=None,
        description="A new currency id. Must be different from the previous one",
    )


class Income(PublicData):
    """The public representation of an income."""

    id: int = Field(description="Unique identifier in the system")
    name: str = Field(description="The name of the currency")
    value: int = Field(description="The value in cents")
    source: domain.transactions.IncomeSource = Field(
        default="revenue", description="Available 'source' for the income."
    )
    timestamp: date = Field(description=("The date of a transaction"))
    currency: Currency


class ExchangeCreateBody(PublicData):
    """The request body to create a new income."""

    from_value: int = Field(description="Given value")
    to_value: int = Field(description="Received value")
    timestamp: date = Field(
        default_factory=date.today, description="The date of a transaction"
    )
    from_currency_id: int = Field(
        description="Internal currency system identifier"
    )
    to_currency_id: int = Field(
        description="Internal currency system identifier"
    )


class ExchangeUpdateBody(PublicData):
    """The request body to update the existing exchange."""

    from_value: int | None = Field(default=None, description="Given value")
    to_value: int | None = Field(default=None, description="Received value")
    timestamp: date | None = Field(
        default=None,
        description="The date of a transaction",
    )
    from_currency_id: int | None = Field(
        default=None, description="Internal currency system identifier"
    )
    to_currency_id: int | None = Field(
        default=None, description="Internal currency system identifier"
    )


class Exchange(PublicData):
    """The public representation of an income."""

    id: int = Field(description="Unique identifier in the system")
    from_value: int
    to_value: int
    timestamp: date = Field(description=("The date of a transaction"))
    from_currency: Currency
    to_currency: Currency
