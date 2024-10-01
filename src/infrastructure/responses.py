from collections.abc import Sequence
from typing import Generic, Literal, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, alias_generators, conlist

ErrorType = Literal["internal", "external", "missing", "bad-type"]


class InternalData(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class PublicData(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
        loc_by_alias=True,
        alias_generator=alias_generators.to_camel,
    )


_TPublicData = TypeVar("_TPublicData", bound=PublicData)


class ResponseMultiPaginated(PublicData, Generic[_TPublicData]):
    """Generic response model that consist multiple results,
    paginated with cursor pagination.
    """

    result: Sequence[_TPublicData]
    context: int = Field(
        description=(
            "The user ID that should be used for the "
            "next request to get proper pagination"
        )
    )
    left: int = Field(description="How many items is left")


class ResponseMulti(PublicData, Generic[_TPublicData]):
    """Generic response model that consist multiple results."""

    result: Sequence[_TPublicData]


class Response(PublicData, Generic[_TPublicData]):
    """Generic response model that consist only one result."""

    result: _TPublicData


# =====================================================================
# error responses
# =====================================================================
class ErrorDetail(PublicData):
    """Error detail model."""

    path: tuple[str | int, ...] = Field(
        description="The path to the field that raised the error",
        default_factory=tuple,
    )
    type: ErrorType = Field(description="The error type", default="internal")


class ErrorResponse(PublicData):
    """Error response model."""

    message: str = Field(description="This field represent the message")
    detail: ErrorDetail = Field(
        description="This field represents error details",
        default_factory=ErrorDetail,
    )


class ErrorResponseMulti(PublicData):
    """The public error respnse model that includes multiple objects."""

    result: conlist(ErrorResponse, min_length=1)  # type: ignore


# =====================================================================
# pagination
# =====================================================================
class OffsetPagination(PublicData):
    """cursor pagination data class."""

    context: int = Field(description="The ID to start limiting")
    limit: int = Field(description="Limit results total items")


def get_offset_pagination_params(
    context: str | None = Query(
        default=None,
        description="The highest id of previously received item list",
    ),
    limit: str | None = Query(
        default=None,
        description="Limit results total items",
    ),
) -> OffsetPagination:
    """FastAPI HTTP GET query params.

    usage:
        ```py
        @router.get("")
        async def controller(
            pagination: CursorPagination = fastapi.Depends(
                get_cursor_pagination_params
            )
        ):
            ...
    """

    if not context:
        _context = 0
    else:
        try:
            _context = int(context)
        except ValueError as error:
            raise error

    if not limit:
        _limit = 10  # default value
    else:
        try:
            _limit = int(limit)
        except ValueError as error:
            raise error

    return OffsetPagination(context=_context, limit=_limit)
