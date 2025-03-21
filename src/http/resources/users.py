from fastapi import APIRouter, Body, Depends

from src import operational as op
from src.domain import users as domain
from src.infrastructure import Response

from ..contracts.users import User, UserConfigurationPartialUpdateRequestBody

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """retrieve current user information information."""

    return Response[User](result=User.model_validate(user))


@router.patch("/configuration")
async def parial_update_user_configuration(
    user: domain.User = Depends(op.authorize),
    body: UserConfigurationPartialUpdateRequestBody = Body(...),
) -> Response[User]:
    """update the user configuration partially."""

    instance: domain.User = await op.user_update(
        user, **body.model_dump(exclude_unset=True)
    )

    return Response[User](result=User.model_validate(instance))
