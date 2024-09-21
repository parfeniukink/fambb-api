from fastapi import APIRouter

from src import contracts, domain
from src.infrastructure.entities import Response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_configraution() -> Response[contracts.User]:
    # TODO: Get the id from the authentication details

    instance: domain.users.User = await domain.users.UserRepository().get(
        id_=1
    )

    return Response[contracts.User](
        result=contracts.User.model_validate(instance)
    )
