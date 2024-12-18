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

    async def add_user(self, candidate: database.User) -> database.User:
        self.command.session.add(candidate)
        return candidate

    async def update_user_configuration(self, user_id: int, **values) -> None:
        """update user configuration fields."""

        query = (
            update(database.User)
            .where(database.User.id == user_id)
            .values(values)
            .returning(database.User)
        )

        await self.command.session.execute(query)
