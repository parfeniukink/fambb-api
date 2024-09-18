
from typing import Iterable

from fastapi import APIRouter, FastAPI


def web_application(
    *_, rest_routers: Iterable[APIRouter], **kwargs
) -> FastAPI:
    """The application factory using FastAPI framework."""

    # Initialize the base FastAPI application
    app = FastAPI(**kwargs)

    # Include REST API routers
    for router in rest_routers:
        app.include_router(router)

    return app
