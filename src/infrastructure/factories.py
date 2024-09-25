from typing import Iterable

from fastapi import APIRouter, FastAPI
from starlette.middleware import _MiddlewareClass


def web_application(
    *_,
    rest_routers: Iterable[APIRouter],
    middlewares: Iterable[tuple[type[_MiddlewareClass], dict]] | None = None,
    **kwargs,
) -> FastAPI:
    """the application factory using FastAPI framework.

    notes:
        positional arguments are not allowed.
    """

    # initialize the base fastapi application
    app = FastAPI(**kwargs)

    # include rest api routers
    for router in rest_routers:
        app.include_router(router)

    # define middlewares using fastapi hook
    if middlewares is not None:
        for middleware_class, options in middlewares:
            app.add_middleware(middleware_class, **options)

    return app
