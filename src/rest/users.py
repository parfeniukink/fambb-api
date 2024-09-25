import asyncio

from fastapi import APIRouter

from src import contracts, domain
from src import operational as op
from src.infrastructure import Response, database

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_retrieve() -> Response[contracts.User]:
    mock_id = 1
    instance: domain.users.User = await op.user_retrieve(id_=mock_id)

    return Response[contracts.User](
        result=contracts.User.model_validate(instance)
    )


@router.get("/debug")
async def user_debug() -> str:
    async with database.transaction():
        await domain.users.UserRepository().add_user(
            candidate=database.User(name="john", token="secret")
        )

        await domain.users.UserRepository().add_user(
            candidate=database.User(name="marry", token="secret")
        )

    async with database.transaction():
        tasks = [
            domain.users.UserRepository().add_user(
                candidate=database.User(name="mark", token="secret")
            ),
            domain.users.UserRepository().add_user(
                candidate=database.User(name="jack", token="secret")
            ),
        ]

        await asyncio.gather(*tasks)

    return "success"
