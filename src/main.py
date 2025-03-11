"""
this file is an application entrypoint.
the overall structure is inspired by DDD (Eric Evans):
    ↓ main (entrypoint)
    ↓ http (presentation tier)
        ↓ resources (endpoints)
        ↓ contracts (data structures)
    ↓ operational (application tier)
    ↓ domain (business model tier)
    ↓ infrastructure (infrastructure tier)
        ↓ database (ORM, tables)
        ↓ config (global configuration)

the main purpose of the application is working with TRANSACTIONS (costs,
incomes, exchanges). to claim analytics based on that information.

so the overall workflow would look next:
1. client save the income transaction
2. client save the cost transaction
3. client claim for analytics (based on previously saved transactions)
    to check the financial state

also, the equity and all the transactions are shared to all users in the system
so each of them can see the transactions themselves, analytics and equity.
on the other hand user settings are not sharable for others.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src import http
from src.config import settings
from src.infrastructure import errors, factories, middleware

logger.add(
    settings.logging.file,
    format=settings.logging.format,
    rotation=settings.logging.rotation,
    compression=settings.logging.compression,
    level=settings.logging.level,
)


exception_handlers = (
    {
        ValueError: errors.value_error_handler,
        RequestValidationError: errors.unprocessable_entity_error_handler,
        HTTPException: errors.fastapi_http_exception_handler,
        errors.BaseError: errors.base_error_handler,
        NotImplementedError: errors.not_implemented_error_handler,
        Exception: errors.unhandled_error_handler,
    }
    if settings.debug is False
    else {}
)

app: FastAPI = factories.asgi_app(
    debug=settings.debug,
    rest_routers=(
        http.users_router,
        http.currencies_router,
        http.analytics_router,
        http.costs_router,
        http.incomes_router,
        http.exchange_router,
    ),
    middlewares=(
        (CORSMiddleware, middleware.FASTAPI_CORS_MIDDLEWARE_OPTIONS),
    ),
    exception_handlers=exception_handlers,
)
