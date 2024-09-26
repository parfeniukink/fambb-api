from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain import users as domain
from src.infrastructure import database, errors

security = HTTPBearer(auto_error=False)


async def authorize(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
):
    if creds is None:
        raise errors.AuthenticationError(
            "Authorization HTTP header is not specified"
        )

    try:
        token: str = creds.credentials
        user: database.User = await domain.UserRepository().user_by_token(
            token
        )
    except errors.NotFoundError:
        raise errors.AuthenticationError("Invalid Token")
    else:
        return user
