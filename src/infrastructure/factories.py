from typing import Iterable

from fastapi import APIRouter, FastAPI


def asgi_app(
    *_,
    rest_routers: Iterable[APIRouter],
    middlewares: Iterable[tuple] | None = None,
    **kwargs,
) -> FastAPI:
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
