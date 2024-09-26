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

    default_currency: Currency | None = None
    default_cost_category: CostCategory | None = None
    common_costs: tuple[str, ...] | None = None
    common_incomes: tuple[str, ...] | None = None


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
            ),
        )
