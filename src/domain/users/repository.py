from collections.abc import AsyncGenerator

from sqlalchemy import Result, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors


class UserRepository(database.Repository):
    async def user_by_id(self, id_: int) -> database.User:
        """search by ``id``."""

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

    async def excluding(self, id_: int) -> database.User:
        """exlude concrete user from results"""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(database.User.id != id_)
                    .options(
                        joinedload(database.User.default_currency),
                        joinedload(database.User.default_cost_category),
                    )
                )
                user: database.User = results.scalars().one()

        return user

    async def user_by_token(self, token: str) -> database.User:
        """search by ``token``."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(database.User.token == token)
                    .options(
                        joinedload(database.User.default_currency),
                        joinedload(database.User.default_cost_category),
                    )
                )
                try:
                    user: database.User = results.scalars().one()
                except NoResultFound as error:
                    raise errors.NotFoundError("Can't find user") from error

        return user

    async def by_cost_threshold_notification(
        self, cost: database.Cost
    ) -> AsyncGenerator[database.User, None]:
        """exclude current user from the search. select users by threshold."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(
                        database.User.id != cost.user_id,
                        cost.value >= database.User.notify_cost_threshold,
                    )
                    .options(
                        joinedload(database.User.default_currency),
                        joinedload(database.User.default_cost_category),
                    )
                )

                for item in results.scalars():
                    yield item

    async def add_user(self, candidate: database.User) -> database.User:
        self.command.session.add(candidate)
        return candidate

    async def update_user(
        self, candidate: database.User, **values
    ) -> database.User:
        """update user configuration fields."""

        query = (
            update(database.User)
            .where(database.User.id == candidate.id)
            .values(values)
            .returning(database.User)
        )

        await self.command.session.execute(query)

        return candidate
