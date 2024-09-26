from fastapi import APIRouter, Depends

from src import operational as op
from src.contracts import User
from src.domain import users as domain
from src.infrastructure import Response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """Retrieve user information information."""

    return Response[User](result=User.model_validate(user))
