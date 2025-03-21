from typing import Any

from src.domain.users import User, UserRepository
from src.infrastructure import database


async def user_retrieve(id_: int) -> User:
    db_insatnce: database.User = await UserRepository().user_by_id(id_=id_)
    user = User.from_instance(db_insatnce)

    return user


async def user_update(user: User, **values: Any) -> User:
    db_instance: database.User = await UserRepository().user_by_id(id_=user.id)

    async with database.transaction():
        updated_instance: database.User = await UserRepository().update_user(
            candidate=db_instance, **values
        )

    return User.from_instance(updated_instance)
