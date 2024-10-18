import contextlib
import functools
from datetime import date

from pydantic import Field, field_validator

from src import domain
from src.infrastructure import PublicData

from .currency import Currency


class _TimestampValidationMixin:
    @field_validator("timestamp", mode="before")
    @classmethod
    def _timestamp_is_valid(cls, value: str | None) -> date | None:
        """check if it is possible to convet the timestamp string."""

        if value is None:
            return value
        else:
            return domain.transactions.timestamp_from_raw(value)


class _ValueValidationMixin:
    @field_validator("value", mode="before")
    @classmethod
    def _value_is_valid(cls, value: float | None):
        """check if the value is convertable to cents."""

        if value is None:
            return value
        else:
            domain.transactions.cents_from_raw(value)
            return value


class Transaction(PublicData):
    """a public representation of any sort of a transaction in
    the system: cost, income, exchange.

    notes:
        This class is mostly for the analytics.
    """

    operation: domain.transactions.OperationType = Field(
        description="The type of the operation"
    )
    name: str = Field(description="The name of the transaction")
    value: float = Field(description="The amount with cents")
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
            value=instance.value_prettified,
            timestamp=instance.timestamp,
            currency=instance.currency.sign,
        )


class CostCategoryCreateBody(PublicData):
    """The request body to create a new cost category."""

    name: str


class CostCategory(CostCategoryCreateBody):
    """The public representation of a cost category."""

    id: int


class CostCreateBody(
    PublicData, _ValueValidationMixin, _TimestampValidationMixin
):
    """The request body to create a new cost."""

    name: str = Field(description="The name of the cost")
    value: float = Field(examples=[12.2, 650])
    timestamp: date = Field(
        default_factory=date.today,
        description=(
            "Define the timestamp for the cost. The default value is 'today'"
        ),
    )
    currency_id: int
    category_id: int

    @property
    def value_in_cents(self):
        return domain.transactions.cents_from_raw(self.value)


class CostUpdateBody(
    PublicData, _ValueValidationMixin, _TimestampValidationMixin
):
    """The request body to update the existing cost."""

    name: str | None = Field(
        default=None,
        description="The name of the currency",
    )
    value: float | None = Field(default=None, examples=[12.2, 650])
    timestamp: date | None = Field(
        default=None,
        description=(
            "Define the timestamp for the cost. The default value is 'null'"
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

    @property
    def value_in_cents(self) -> int | None:
        with contextlib.suppress(ValueError):
            return domain.transactions.cents_from_raw(self.value)

        return None


class Cost(PublicData):
    """The public representation of a cost."""

    id: int = Field(description="Unique identifier in the system")
    name: str = Field(description="The name of the cost")
    value: float = Field(examples=[12.2, 650])
    timestamp: date = Field(description=("The date of a transaction"))
    currency: Currency
    category: CostCategory


class IncomeCreateBody(
    PublicData, _ValueValidationMixin, _TimestampValidationMixin
):
    """The request body to create a new income."""

    name: str = Field(description="The name of the income")
    value: float = Field(examples=[12.2, 650])
    source: domain.transactions.IncomeSource = Field(
        default="revenue", description="Available 'source' for the income."
    )
    timestamp: date = Field(
        default_factory=date.today,
        description=("The date of a transaction"),
    )
    currency_id: int = Field(description="Internal currency system identifier")

    @property
    def value_in_cents(self) -> int:
        """return the value but in cents."""

        return domain.transactions.as_cents(self.value)


class IncomeUpdateBody(
    PublicData, _ValueValidationMixin, _TimestampValidationMixin
):
    """The request body to update the existing income."""

    name: str | None = Field(
        default=None,
        description="The name of the income",
    )
    value: float | None = Field(default=None, examples=[12.2, 650])
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
    name: str = Field(description="The name of the income")
    value: float = Field(examples=[12.2, 650])
    source: domain.transactions.IncomeSource = Field(
        description="Available 'source' for the income."
    )
    timestamp: date = Field(description=("The date of a transaction"))
    currency: Currency


class ExchangeCreateBody(PublicData, _TimestampValidationMixin):
    """The request body to create a new income."""

    from_value: float = Field(description="Given value")
    to_value: float = Field(description="Received value")
    timestamp: date = Field(
        default_factory=date.today, description=("The date of a transaction")
    )
    from_currency_id: int = Field(
        description="Internal currency system identifier"
    )
    to_currency_id: int = Field(
        description="Internal currency system identifier"
    )

    @property
    def from_value_in_cents(self) -> int:
        """return the value but in cents."""

        return int(self.from_value * 100)

    @property
    def to_value_in_cents(self) -> int:
        """return the value but in cents."""

        return int(self.to_value * 100)

    @field_validator("from_value", "to_value", mode="before")
    @classmethod
    def _validate_money_values(cls, value: float) -> float:
        """check if the value is convertable to cents."""

        domain.transactions.cents_from_raw(value)
        return value


class ExchangeUpdateBody(PublicData, _TimestampValidationMixin):
    """The request body to update the existing exchange."""

    from_value: float | None = Field(default=None, description="Given value")
    to_value: float | None = Field(default=None, description="Received value")
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

    @field_validator("from_value", "to_value", mode="before")
    @classmethod
    def _validate_money_values(cls, value: float | None) -> float | None:
        """check if the value is convertable to cents."""

        if value is None:
            return value
        else:
            domain.transactions.cents_from_raw(value)
            return value


class Exchange(PublicData):
    """The public representation of an income."""

    id: int = Field(description="Unique identifier in the system")
    from_value: float = Field(description="Given value")
    to_value: float = Field(description="Received value")
    timestamp: date = Field(description=("The date of a transaction"))
    from_currency: Currency
    to_currency: Currency
