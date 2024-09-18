from typing import Protocol

from starlette.types import Receive, Scope, Send

from src.config import settings


class Middleware(Protocol):
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None: ...


# NOTE: For more information:
#       fastapi.middleware.cors.CORSMiddleware
FASTAPI_CORS_MIDDLEWARE_OPTIONS: dict = {
    "allow_origins": settings.cors.allow_origins,
    "allow_credentials": settings.cors.allow_credentials,
    "allow_methods": settings.cors.allow_methods,
    "allow_headers": settings.cors.allow_headers,
    "expose_headers": settings.cors.expose_headers,
    "max_age": settings.cors.max_age,
}
