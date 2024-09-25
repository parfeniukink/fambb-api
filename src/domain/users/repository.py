from typing import Any

from loguru import logger
from sqlalchemy import Result, Select, func, select
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors


class UserRepository(database.Repository):
    async def get_user(self, id_: int) -> database.User:
        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(database.User.id == id_)
                    .options(
                        joinedload(database.User.default_currency),
                        joinedload(database.User.default_cost_category),
                    )
                )
                user: database.User = results.scalars().one()
                return user

    async def add_user(self, candidate: database.User) -> database.User:
        self.command.session.add(candidate)
        return candidate

    async def count_users(self) -> int:
        query: Select = select(func.count(database.User.id))

        async with self.query.session as session:
            async with session.begin():
                result: Result = await session.execute(query)
                value: Any = result.scalar()

                if not isinstance(value, int):
                    raise errors.DatabaseError(
                        message=(
                            "Database count() function returned no-integer "
                            f"({type(value)}) type of value"
                        ),
                    )
                else:
                    return value
