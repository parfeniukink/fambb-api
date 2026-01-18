"""
notes:
    ``src.domain.equity`` and ``src.domain.transactions`` are not used
    from 'Bounded Context' due to the MVP simplicity.
"""

import functools

from src.domain.equity import Currency
from src.domain.transactions import CostCategory
from src.infrastructure import InternalData, database


class UserConfiguration(InternalData):
    """User configuration is a part of a ``users`` table."""

    show_equity: bool = False
    default_currency: Currency | None = None
    default_cost_category: CostCategory | None = None
    cost_snippets: list[str] | None = None
    income_snippets: list[str] | None = None

    last_notification: str | None = None
    notify_cost_threshold: int | None = None

    monobank_api_key: str | None = None


class User(InternalData):
    """Extended user data object with configuration details."""

    id: int
    name: str
    token: str
    configuration: UserConfiguration

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
                cost_snippets=instance.cost_snippets,
                income_snippets=instance.income_snippets,
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
                last_notification=instance.last_notification,
                notify_cost_threshold=instance.notify_cost_threshold,
                monobank_api_key=instance.monobank_api_key,
            ),
        )
