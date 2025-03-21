from pydantic import Field, field_validator

from src import domain
from src.infrastructure import PublicData

from .currency import Currency
from .transactions import CostCategory


class UserConfiguration(PublicData):
    show_equity: bool = Field(
        default=False, description="Define if the equity is visible"
    )
    default_currency: Currency | None = Field(
        default=None, description="A default currency costs and incomes"
    )
    default_cost_category: CostCategory | None = Field(
        default=None, description="A default currency costs and incomes"
    )
    cost_snippets: list[str] | None = Field(
        default=None,
        description="The list of available snippets for the cost name",
    )
    income_snippets: list[str] | None = Field(
        default=None,
        description="The list of available snippets for the income name",
    )
    notify_cost_threshold: float | None = Field(
        default=None,
        description=(
            "The thrashhold for the value, to be notified "
            "about costs. NOT in CENTS"
        ),
    )
    pagination_items: int = Field(
        default=10,
        description="A number of paginated items in transactions analytics",
    )

    @field_validator("notify_cost_threshold", mode="after")
    @classmethod
    def notify_cost_threshold_prettify(
        cls, value: float | None
    ) -> float | None:
        if value is not None:
            return domain.transactions.pretty_money(value)
        else:
            return value


class UserConfigurationPartialUpdateRequestBody(PublicData):
    show_equity: bool = Field(
        default=False, description="Define if the equity is visible"
    )
    default_currency_id: int | None = Field(
        default=None, description="Update the default_currency_id"
    )
    default_cost_category_id: int | None = Field(
        default=None, description="Update the default_cost_category_id"
    )
    cost_snippets: list[str] | None = Field(
        default=None,
        description="A list of available snippets for the cost name",
    )
    income_snippets: list[str] | None = Field(
        default=None,
        description="A list of available snippets for the income name",
    )
    notify_cost_threshold: float | None = Field(
        default=None,
        description="A thrashhold to be notified about others costs",
    )
    pagination_items: int | None = Field(
        default=None,
        description="A number of paginated items in transactions analytics",
    )

    @field_validator("notify_cost_threshold", mode="after")
    @classmethod
    def notify_cost_threshold_to_cents(cls, value: float | None) -> int | None:
        if value is not None:
            return domain.transactions.cents_from_raw(value)
        else:
            return value


class UserCreateRequestBody(PublicData):
    """create a new user HTTP request body schema."""

    name: str


class User(PublicData):
    id: int
    name: str
    configuration: UserConfiguration = UserConfiguration()
