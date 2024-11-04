from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src import rest
from src.config import settings
from src.infrastructure import errors, factories, middleware

# adjust the logging
# -------------------------------
logger.add(
    settings.logging.file,
    format=settings.logging.format,
    rotation=settings.logging.rotation,
    compression=settings.logging.compression,
    level=settings.logging.level,
)


# adjust the application
# -------------------------------
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

app: FastAPI = factories.web_application(
    debug=settings.debug,
    rest_routers=(
        rest.analytics.router,
        rest.costs.router,
        rest.incomes.router,
        rest.exchange.router,
        rest.currencies.router,
        rest.users.router,
    ),
    middlewares=(
        (CORSMiddleware, middleware.FASTAPI_CORS_MIDDLEWARE_OPTIONS),
    ),
    exception_handlers=exception_handlers,
)
