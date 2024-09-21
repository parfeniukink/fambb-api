from collections.abc import AsyncGenerator

from tests.mock_storage import Storage

from src.domain.finances import Currency
from src.domain.transactions import CostCateogoryFlat

from .aggregates import User
from .entities import UserConfiguration, UserDBCandidate


class UserRepository:
    async def get(self, id_: int) -> User:
        if not (user := Storage.users.get(id_)):
            raise Exception(f"User {id_} not found")

        default_currency: Currency | None = (
            Currency(**Storage.currencies[currency_id])
            if (currency_id := user.get("default_currency_id"))
            else None
        )
        default_category: CostCateogoryFlat | None = (
            CostCateogoryFlat(**Storage.cost_categories[category_id])
            if (category_id := user.get("default_category_id"))
            else None
        )

        return User(
            id=id_,
            name=user["name"],
            configuration=UserConfiguration(
                default_currency=default_currency,
                default_category=default_category,
                common_costs=(
                    tuple(user["common_costs"].split(","))
                    if user["common_costs"]
                    else ()
                ),
                common_incomes=(
                    tuple(user["common_incomes"].split(","))
                    if user["common_incomes"]
                    else ()
                ),
            ),
        )

    async def add_user(self, candidate: UserDBCandidate) -> User:
        new_id = max(Storage.users.keys()) + 1
        instance: dict = dict(
            id=new_id,
            name=candidate.name,
            default_category_id=None,
            default_currency_id=None,
            cost_names=None,
            income_names=None,
        )
        Storage.users[new_id] = instance

        return await self.get(id_=instance["id"])
