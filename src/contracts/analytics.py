from typing import Generic

from pydantic import Field

from src.infrastructure import PublicData, _TPublicData

from .transactions import Cost, Exchange, Income


class ChartSection(PublicData, Generic[_TPublicData]):
    items: list[_TPublicData]
    total: int


class ChartMath(PublicData):
    costs_to_incomes: float = Field(
        description=(
            "Belongs to sum(costs) / sum(incomes). "
            "The overall analytic. Does not include any extra filters"
        )
    )


class Chart(PublicData):
    """represents the independent chat information"""

    costs: ChartSection[Cost]
    incomes: ChartSection[Income]
    exchanges: ChartSection[Exchange]
    math: ChartMath
