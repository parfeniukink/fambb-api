import contextlib

from pydantic import Field

from src import domain
from src.infrastructure import PublicData

from ._mixins import _ValueValidationMixin


class CostShortcutCreateBody(PublicData, _ValueValidationMixin):
    """The request body to create a new cost."""

    name: str = Field(description="The name of the cost")
    value: float | None = Field(default=None, examples=[12.2, 650, None])
    currency_id: int
    category_id: int

    @property
    def value_in_cents(self) -> int | None:
        with contextlib.suppress(ValueError):
            return domain.transactions.cents_from_raw(self.value)

        return None


class CostShortcut(CostShortcutCreateBody):
    id: int
