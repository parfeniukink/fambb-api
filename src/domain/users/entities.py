"""
notes:
    ``src.domain.equity`` and ``src.domain.transactions`` are not used
    from 'Bounded Context' due to the MVP simplicity.
"""

import functools

from pydantic import Field

from src.domain.equity import Currency
from src.domain.transactions import CostCategory
from src.infrastructure import Bank, InternalData, database, errors


class UserConfiguration(InternalData):
    """User configuration is a part of a ``users`` table."""

    show_equity: bool = False
    default_currency: Currency | None = None
    default_cost_category: CostCategory | None = None
    cost_snippets: tuple[str, ...] | None = None
    income_snippets: tuple[str, ...] | None = None
    notify_cost_threshold: int | None = None


class BankMetadata(InternalData):
    bank: Bank
    api_key: str | None = None
    transactions_history: set[str] | None = None


class User(InternalData):
    """Extended user data object with configuration details."""

    id: int
    name: str
    token: str
    configuration: UserConfiguration
    bank_metadata: list[BankMetadata] = Field(default_factory=list)

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "User":
        raise NotImplementedError(
            f"Can not get {cls.__name__} from {type(instance)} type"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.User):
        return cls(
            id=instance.id,
            name=instance.name,
            token=instance.token,
            configuration=UserConfiguration(
                show_equity=instance.show_equity,
                cost_snippets=(
                    tuple(instance.cost_snippets)
                    if instance.cost_snippets
                    else None
                ),
                income_snippets=(
                    tuple(instance.income_snippets)
                    if instance.income_snippets
                    else None
                ),
                default_currency=(
                    Currency.from_instance(instance.default_currency)
                    if instance.default_currency
                    else None
                ),
                default_cost_category=(
                    CostCategory.model_validate(instance.default_cost_category)
                    if instance.default_cost_category
                    else None
                ),
                notify_cost_threshold=instance.notify_cost_threshold,
            ),
            bank_metadata=[],  # todo: implement
        )

    def get_bank_metadata(self, bank: Bank) -> BankMetadata:
        for item in self.bank_metadata:
            if item.bank == bank:
                return item

        raise errors.BadRequestError(
            f"{bank.capitalize()} Metadata is not set. More on "
            "`HTTP PATCH /identity/users/configuration`"
        )
