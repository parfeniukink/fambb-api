from pydantic import Field

from src.infrastructure import PublicData

from .currency import Currency
from .transactions import CostCategory


class UserConfiguration(PublicData):
    default_currency: Currency | None = Field(
        default=None, description="A default currency costs and incomes"
    )
    default_category: CostCategory | None = Field(
        default=None, description="A default currency costs and incomes"
    )
    common_costs: tuple[str, ...] | None = Field(
        default=None,
        description="A common costs list to be used as a placeholder, etc",
    )
    common_incomes: tuple[str, ...] | None = Field(
        default=None,
        description="A common incomes list to be used as a placeholder, etc",
    )


class UserCreateRequestBody(PublicData):
    """create a new user HTTP request body schema."""

    name: str


class User(PublicData):
    id: int
    name: str
    configuration: UserConfiguration = UserConfiguration()
