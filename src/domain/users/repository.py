from sqlalchemy import Result, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors


class UserRepository(database.Repository):
    async def user_by_id(self, id_: int):
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

    async def user_by_token(self, token: str):
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
