import asyncio
from typing import Any

from src.domain.users import User, UserRepository
from src.infrastructure import database


async def user_retrieve(id_: int) -> User:
    db_insatnce: database.User = await UserRepository().user_by_id(id_=id_)
    user = User.from_instance(db_insatnce)

    return user


async def user_update(user: User, **values: Any) -> User:
    """update user and all related details.

    FLOW
    - separate update payloads to bank payloads and user payload

    NOTES
    - updating user includes updating bank integrations as well

    """

    repo = UserRepository()
    tasks = set()

    # extract API Keys from the payload
    if "monobank_api_key" in values:
        monobank_api_key = values.pop("monobank_api_key", None)
        tasks.add(repo.set_api_key(user.id, "monobank", monobank_api_key))

    if values:
        tasks.add(repo.update_user(user.id, **values))

    async with database.transaction():
        await asyncio.gather(*tasks)

    instance: database.User = await UserRepository().user_by_id(user.id)

    return User.from_instance(instance)
