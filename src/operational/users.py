from typing import Any

from src.domain.users import User, UserRepository
from src.infrastructure import database


async def user_retrieve(id_: int) -> User:
    db_insatnce: database.User = await UserRepository().user_by_id(id_=id_)
    user = User.from_instance(db_insatnce)

    return user


async def user_update(user: User, **values: Any) -> User:
    repo = UserRepository()

    async with database.transaction():
        await repo.update_user(user.id, **values)

    db_instance = await repo.user_by_id(user.id)

    return User.from_instance(db_instance)
