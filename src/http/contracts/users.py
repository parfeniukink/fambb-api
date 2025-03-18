import functools

from pydantic import Field

from src import domain
from src.infrastructure import PublicData, database

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
    notify_cost_threshold: int | None = Field(
        default=None,
        description="The thrashhold for the value, to be notified about costs",
    )
    pagination_items: int = Field(
        default=10,
        description="A number of paginated items in transactions analytics",
    )


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
    notify_cost_threshold: int | None = Field(
        default=None,
        description="A thrashhold to be notified about others costs",
    )
    pagination_items: int | None = Field(
        default=None,
        description="A number of paginated items in transactions analytics",
    )


class UserCreateRequestBody(PublicData):
    """create a new user HTTP request body schema."""

    name: str


class User(PublicData):
    id: int
    name: str
    configuration: UserConfiguration = UserConfiguration()

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
            configuration=UserConfiguration(
                show_equity=instance.show_equity,
                cost_snippets=instance.cost_snippets,
                income_snippets=instance.income_snippets,
                default_currency=(
                    Currency(
                        id=currency.id,
                        name=currency.name,
                        sign=currency.sign,
                    )
                    if (currency := instance.default_currency)
                    else None
                ),
                default_cost_category=(
                    CostCategory(
                        id=cost_category.id,
                        name=cost_category.name,
                    )
                    if (cost_category := instance.default_cost_category)
                    else None
                ),
                notify_cost_threshold=instance.notify_cost_threshold,
            ),
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.users.User):
        return User.model_validate(instance)
