__all__ = ("settings",)

from pathlib import Path
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CORSSettings(BaseModel):
    allow_origins: list[AnyHttpUrl | Literal["*"]] = ["*"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = True
    expose_headers: list[str] = []
    max_age: int = 600


class LoggingSettings(BaseModel):
    """Configure the logging engine."""

    # The time field can be formatted using more human-friendly tokens.
    # These constitute a subset of the one used by the Pendulum library
    # https://pendulum.eustace.io/docs/#tokens
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {message}"
    level: str = "INFO"
    file: str = "/tmp/fambb.log"
    rotation: str = "10MB"
    compression: str = "zip"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    debug: bool = False

    cors: CORSSettings = CORSSettings()
    logging: LoggingSettings = LoggingSettings()


settings = Settings()
