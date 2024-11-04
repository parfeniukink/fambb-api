from fastapi import APIRouter, Body, Depends

from src import operational as op
from src.contracts import User, UserConfigurationUpdateRequestBody
from src.domain import users as domain
from src.infrastructure import Response, database

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """Retrieve user information information."""

    return Response[User](result=User.from_instance(user))


@router.put("/configuration")
async def update_user_configuration(
    user: domain.User = Depends(op.authorize),
    body: UserConfigurationUpdateRequestBody = Body(...),
) -> None:
    """Update the user configuration partially."""

    async with database.transaction():
        await domain.UserRepository().update_user_configuration(
            user_id=user.id, **body.model_dump(exclude_unset=True)
        )
