import functools

from pydantic import Field

from src import domain
from src.infrastructure import database
from src.infrastructure.responses import PublicData

from .currency import Currency


class CashBalanceCreateBody(PublicData):
    """Request body to create a new cash balance card."""

    currency_id: int = Field(description="Currency to track")
    step: float = Field(
        description="Increment/decrement step",
        gt=0,
    )

    @property
    def step_in_cents(self) -> int:
        return int(round(self.step * 100, 2))


class CashBalanceUpdateBody(PublicData):
    """Request body to update an existing cash card."""

    balance: float | None = Field(
        default=None,
        description="New absolute balance",
        ge=0,
    )
    step: float | None = Field(
        default=None,
        description="New step value",
        gt=0,
    )

    @property
    def balance_in_cents(self) -> int | None:
        if self.balance is not None:
            return int(round(self.balance * 100, 2))
        return None

    @property
    def step_in_cents(self) -> int | None:
        if self.step is not None:
            return int(round(self.step * 100, 2))
        return None


class CashBalance(PublicData):
    """Public representation of a cash balance card."""

    id: int = Field(description="Unique identifier in the system")
    currency: Currency
    balance: float = Field(description="Current balance")
    step: float = Field(description="Increment/decrement step")

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "CashBalance":
        raise NotImplementedError(
            f"Can not convert {type(instance)} "
            f"into the {cls.__name__} contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.CashBalance):
        return cls(
            id=instance.id,
            currency=Currency.model_validate(instance.currency),
            balance=domain.transactions.pretty_money(instance.balance),
            step=domain.transactions.pretty_money(instance.step),
        )
