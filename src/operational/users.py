from src.domain.users import User, UserRepository
from src.infrastructure import database


async def user_retrieve(id_: int) -> User:
    db_insatnce: database.User = await UserRepository().get_user(id_=id_)
    user = User.from_instance(db_insatnce)

    return user


# async def user_create(id_: int, user_payload):
#     async with database.transaction():
#         insatnce: database.User = await domain.users.UserRepository().add_user(
#             candidate=database.User()
#         )
#         user = domain.users.User.from_insatnce(insatnce)

#     return user
