from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, alias_generators, conlist

ErrorType = Literal["internal", "external"]


class InternalData(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


_TInternalData = TypeVar("_TInternalData", bound=InternalData)


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


class ResponseMulti(PublicData, Generic[_TPublicData]):
    """Generic response model that consist multiple results."""

    result: list[_TPublicData]


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
