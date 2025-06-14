from fastapi import APIRouter, Body, Depends

from src import operational as op
from src.domain import users as domain
from src.infrastructure import Response

from ..contracts.identity import (
    AuthorizeRequestBody,
    Identity,
    User,
    UserConfigurationPartialUpdateRequestBody,
)

router = APIRouter(prefix="/identity", tags=["Identity"])


@router.post("/auth")
async def authorize(
    body: AuthorizeRequestBody = Body(...),
) -> Response[Identity]:
    """authorize user with credentials."""

    user: domain.User = await op.authorize_with_token(body.token)

    return Response[Identity](
        result=Identity(
            user=User.model_validate(user), access_token=user.token
        )
    )


@router.get("/users")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """retrieve current user information information."""

    return Response[User](result=User.from_instance(user))


@router.patch("/users/configuration")
async def parial_update_user_configuration(
    user: domain.User = Depends(op.authorize),
    body: UserConfigurationPartialUpdateRequestBody = Body(...),
) -> Response[User]:
    """update the user configuration partially."""

    instance: domain.User = await op.user_update(
        user, **body.model_dump(exclude_unset=True)
    )

    return Response[User](result=User.model_validate(instance))
