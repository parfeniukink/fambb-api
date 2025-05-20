from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain import users as domain
from src.infrastructure import database, errors

security = HTTPBearer(auto_error=False)


async def authorize_with_token(token: str) -> domain.User:
    try:
        user: database.User = await domain.UserRepository().user_by_token(
            token
        )
    except errors.NotFoundError as error:
        raise errors.AuthenticationError("Invalid Token") from error
    else:
        return domain.User.from_instance(user)


async def authorize(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> domain.User:
    """dependency-injection for FastAPI."""

    if creds is None:
        raise errors.AuthenticationError(
            "Authorization HTTP header is not specified"
        )
    else:
        return await authorize_with_token(creds.credentials)
