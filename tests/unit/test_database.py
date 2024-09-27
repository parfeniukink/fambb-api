import asyncio
import random
import string
import uuid

import pytest

from src import domain
from src.infrastructure import database, errors


@pytest.mark.use_db
async def test_database_transactions_separate_success():
    async with database.transaction() as session:
        first_user = await domain.users.UserRepository().add_user(
            candidate=database.User(
                name=random.choice(string.ascii_letters),
                token=str(uuid.uuid4()),
            )
        )

        await session.flush()  # to get first_user's id
        assert (
            first_user.id is not None
        ), "user id is not populated after flushing"

        await domain.users.UserRepository().add_user(
            candidate=database.User(
                name=random.choice(string.ascii_letters),
                token=str(uuid.uuid4()),
            )
        )

    users_total: int = await domain.users.UserRepository().count(database.User)

    assert users_total == 2, f"received {users_total} users. expected 2"


@pytest.mark.use_db
async def test_database_transactions_gathered_success():
    async with database.transaction():
        tasks = [
            domain.users.UserRepository().add_user(
                candidate=database.User(
                    name=random.choice(string.ascii_letters),
                    token=str(uuid.uuid4()),
                )
            )
            for _ in range(2)
        ]
        await asyncio.gather(*tasks)

    users_total: int = await domain.users.UserRepository().count(database.User)

    assert users_total == 2, f"received {users_total} users. expected 2"


@pytest.mark.use_db
async def test_database_transactions_rollback():
    """check if session transaction works correctly.

    notes:
        if error was raise at the same transaction block user should not
        exist in the database.
    """

    with pytest.raises(errors.DatabaseError):
        async with database.transaction():
            await domain.users.UserRepository().add_user(
                candidate=database.User(
                    name="john",
                    token="41d917c7-464f-4056-b2de-1a6e2fbfd9e7",
                )
            )

            def raise_exception():
                raise Exception("Some exception")

            raise_exception()

    async with database.transaction():
        await domain.users.UserRepository().add_user(
            candidate=database.User(
                name="john",
                token="ae9abc17-6b22-4bc0-a127-8b7ba91e99dc",
            )
        )

    john = await domain.users.UserRepository().user_by_id(1)

    assert john.name == "john"
    assert john.token == "ae9abc17-6b22-4bc0-a127-8b7ba91e99dc"
