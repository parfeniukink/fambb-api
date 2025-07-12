from collections.abc import AsyncGenerator, Sequence

from sqlalchemy import Result, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from src.infrastructure import Bank, database, errors


class UserRepository(database.Repository):
    async def user_by_id(self, id_: int) -> database.User:
        """search by ``id``."""

        async with self.query.session as session:
            async with session.begin():
                results: Result = await session.execute(
                    select(database.User)
                    .where(database.User.id == id_)
                    .options(
                        selectinload(database.User.default_currency),
                        selectinload(database.User.default_cost_category),
                        selectinload(database.User.bank_metadata),
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
                        selectinload(database.User.default_currency),
                        selectinload(database.User.default_cost_category),
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
                        selectinload(database.User.default_currency),
                        selectinload(database.User.default_cost_category),
                        selectinload(database.User.bank_metadata),
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
            results: Result = await session.execute(
                select(database.User)
                .where(
                    database.User.id != cost.user_id,
                    cost.value >= database.User.notify_cost_threshold,
                )
                .options(
                    selectinload(database.User.default_currency),
                    selectinload(database.User.default_cost_category),
                )
            )

            for item in results.scalars():
                yield item

    async def add_user(self, candidate: database.User) -> database.User:
        self.command.session.add(candidate)
        await self.command.session.flush()

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

    async def set_api_key(
        self, user_id: int, bank: Bank, api_key: str
    ) -> None:

        query = (
            insert(database.BankMetadata)
            .values(user_id=user_id, bank=bank, api_key=api_key)
            .on_conflict_do_update(
                index_elements=["user_id", "bank"], set_={"api_key": api_key}
            )
        )

        await self.command.session.execute(query)

    async def update_bank_transactions_history(
        self, user_id: int, bank: Bank, history: set[str]
    ) -> None:
        query = (
            update(database.BankMetadata)
            .where(
                database.BankMetadata.user_id == user_id,
                database.BankMetadata.bank == bank,
            )
            .values(transactions_history=history)
        )

        await self.command.session.execute(query)
