from src.domain.users import User, UserRepository
from src.infrastructure import database


async def user_retrieve(id_: int) -> User:
    db_insatnce: database.User = await UserRepository().user_by_id(id_=id_)
    user = User.from_instance(db_insatnce)

    return user
