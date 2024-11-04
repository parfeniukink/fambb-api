"""
module with fastapi error handlers
that are dispatched automatically by fastapi engine.


todo:
 - [ ] add handler for invalid `Literal` query parameters
"""

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette import status
from starlette.requests import Request

from ..responses import (
    ErrorDetail,
    ErrorResponse,
    ErrorResponseMulti,
    ErrorType,
)
from .exceptions import BaseError


def fastapi_to_internal_error_mapper(value: str) -> ErrorType:
    """maps ValidationError, HTTPException, other exceptions occured
    in the runtime to internal error types.

    notes:
        ``internal`` stand for overall internal error. aka Exception in Python
        ``external`` stand for external API/Service issue
        ``missing`` some data is missed
        ``bad-type`` some fields has wrong data types
    """

    if value == "missing":
        return "missing"
    elif "_type" in value:
        return "bad-type"
    else:
        return "internal"


def unprocessable_entity_error_handler(
    _: Request, error: RequestValidationError
) -> JSONResponse:
    """This function is called if the request validation is not passed.
    This error is raised automatically by FastAPI.
    """

    response = ErrorResponseMulti(
        result=[
            ErrorResponse(
                message=err["msg"],
                detail=ErrorDetail(
                    path=err["loc"],
                    type=fastapi_to_internal_error_mapper(err["type"]),
                ),
            )
            for err in error.errors()
        ]
    )
    logger.debug(error.errors()[0]["type"])
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        content=jsonable_encoder(response.model_dump(by_alias=True)),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def value_error_handler(_: Request, error: ValueError) -> JSONResponse:
    response = ErrorResponse(message=str(error))
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        content=jsonable_encoder(response.model_dump(by_alias=True)),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def fastapi_http_exception_handler(
    _: Request, error: HTTPException
) -> JSONResponse:
    """This function is called if the HTTPException was raised."""

    response = ErrorResponse(message=error.detail)
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        content=response.model_dump(by_alias=True),
        status_code=error.status_code,
    )


def not_implemented_error_handler(
    _: Request, error: NotImplementedError
) -> JSONResponse:
    """This function is called if the NotImplementedError was raised."""
    response = ErrorResponse(message=str(error) or "⚠️ Work in progress")
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        content=response.model_dump(by_alias=True),
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )


def database_error_handler(
    _: Request, error: NotImplementedError
) -> JSONResponse:
    """This function is called if the NotImplementedError was raised."""
    response = ErrorResponse(message="Database error occurred")
    logger.error(error)

    return JSONResponse(
        content=response.model_dump(by_alias=True),
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )


def base_error_handler(_: Request, error: BaseError) -> JSONResponse:
    """This function handles all errors that are inherited from BaseError.
    Each class that inherits the BaseError has a status_code attribute.
    """

    response = ErrorResponse(message=str(error))
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        response.model_dump(by_alias=True),
        status_code=error.status_code,
    )


def unhandled_error_handler(_: Request, error: Exception) -> JSONResponse:
    response = ErrorResponse(message=str(error))
    logger.error(response.model_dump(by_alias=True))

    return JSONResponse(
        response.model_dump(by_alias=True),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
