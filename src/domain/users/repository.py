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

    # TODO: convert to `user(**filters)`
    async def user_by_name(self, name: str) -> database.User:
        """search by ``name`` for login lookup."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(database.User.name == name)
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

    async def update_user(self, id_: int, **values) -> None:
        """update user configuration fields.

        IMPROVEMENTS
        1. ``query = query.returning(database.User)``
        2. ``self.command.session.execute``
        3. pass ``candidate`` instead of user id (kind of 'select for update')
        4. todo: add availability for the query descriptor to get
                 the SESSION that is created in ``database.transaction()``
        """

        query = (
            update(database.User).where(database.User.id == id_).values(values)
        )

        await self.command.session.execute(query)
