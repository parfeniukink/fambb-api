from datetime import date

from pydantic import field_validator

from src import domain


class _TimestampValidationMixin:
    @field_validator("timestamp", mode="before")
    @classmethod
    def _timestamp_is_valid(cls, value: str | None) -> date | None:
        """check if it is possible to convet the timestamp string."""

        if value is not None:
            return domain.transactions.timestamp_from_raw(value)

        return value


class _ValueValidationMixin:
    @field_validator("value", mode="before")
    @classmethod
    def _value_is_valid(cls, value: float | None):
        """check if the value is convertable to cents."""

        if value is not None:
            domain.transactions.cents_from_raw(value)

        return value
