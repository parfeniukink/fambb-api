from fastapi import APIRouter, Body, Depends

from src import operational as op
from src.contracts import User, UserConfigurationPartialUpdateRequestBody
from src.domain import users as domain
from src.infrastructure import Response, database

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/echo")
async def echo() -> str:
    message = "pong"
    return message


@router.get("")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """Retrieve user information information."""

    response = Response[User](result=User.from_instance(user))
    return response


@router.patch("/configuration")
async def parial_update_user_configuration(
    user: domain.User = Depends(op.authorize),
    body: UserConfigurationPartialUpdateRequestBody = Body(...),
) -> None:
    """Update the user configuration partially."""

    # TODO: snippets should be updatable

    async with database.transaction():
        await domain.UserRepository().update_user_configuration(
            user_id=user.id, **body.model_dump(exclude_unset=True)
        )
