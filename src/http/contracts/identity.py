import functools

from pydantic import Field, field_validator

from src import domain
from src.infrastructure import PublicData
from src.infrastructure.types import Bank

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

    @field_validator("notify_cost_threshold", mode="after")
    @classmethod
    def notify_cost_threshold_prettify(
        cls, value: float | None
    ) -> float | None:
        if value is not None:
            return domain.transactions.pretty_money(value)
        else:
            return value


class UserPartialUpdateRequestBody(PublicData):
    """aggregated structure to update all the settings, related to the user"""

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


class UserIntegrations(PublicData):
    monobank_api_key_is_set: bool = Field(
        default=False,
        description=(
            "Defines if Monobank API Key is set for the user. "
            "Look ``HTTP PATCH /identity/users/configuration``"
        ),
    )


class User(PublicData):
    id: int
    name: str
    configuration: UserConfiguration = UserConfiguration()
    integrations: UserIntegrations = UserIntegrations()

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "User":
        raise NotImplementedError(
            f"Can not get {cls.__name__} from {type(instance)} type"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: domain.users.User):
        integrations: dict[Bank, domain.users.BankMetadata] = {
            item.bank: item for item in instance.bank_metadata
        }

        # extract metadata for each bank provider
        monobank_metadata = integrations.get("monobank", None)

        return cls(
            **instance.model_dump(),
            integrations=UserIntegrations(
                monobank_api_key_is_set=(
                    True
                    if (monobank_metadata and monobank_metadata.api_key)
                    else False
                )
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
