from pydantic import Field

from src.domain.finances import Currency
from src.domain.transactions import CostCateogoryFlat
from src.infrastructure.entities import InternalData


class UserDBCandidate(InternalData):
    """Database candidate representation."""

    name: str


class UserFlat(UserDBCandidate):

    id: int


class UserConfiguration(InternalData):
    """User configuration is a part of a ``users`` table."""

    default_currency: Currency | None = None
    default_category: CostCateogoryFlat | None = None
    common_costs: tuple[str, ...] | None = None
    common_incomes: tuple[str, ...] | None = None
