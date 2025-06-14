import functools

from pydantic import Field, field_validator

from src import domain
from src.infrastructure import PublicData

from .currency import Currency
from .transactions import CostCategory


# ─────────────────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────────────────
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

    monobank_api_key_is_set: bool = Field(
        default=False,
        description=(
            "Monobank API Key is not exposed. "
            "You can only see that it is set"
        ),
    )

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "UserConfiguration":
        raise NotImplementedError(
            f"Can not get {cls.__name__} from {type(instance)} type"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.users.UserConfiguration):
        return cls(
            monobank_api_key_is_set=(
                True if instance.monobank_api_key else False
            ),
            **instance.model_dump(),
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
    monobank_api_key: str | None = Field(
        default=None,
        description="Monobank API Key. https://api.monobank.ua/index.html",
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

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "User":
        raise NotImplementedError(
            f"Can not get {cls.__name__} from {type(instance)} type"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.users.User):
        return cls(
            id=instance.id,
            name=instance.name,
            configuration=UserConfiguration.from_instance(
                instance.configuration
            ),
        )


# ─────────────────────────────────────────────────────────
# AUTHORIZATION
# ─────────────────────────────────────────────────────────
class AuthorizeRequestBody(PublicData):
    """claim for access token with user credentials.

    NOTES
    -----
    simplified flow is used to authorize the user.
    login will be used.


    FUTURE CHANGES
    -----
    use JWT with login/password
    """

    token: str = Field(description="User's unique token")


class Identity(PublicData):
    access_token: str = Field(
        description="Currently just a unique token of the user"
    )
    user: User
