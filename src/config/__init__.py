__all__ = ("settings",)

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    driver: str = "postgresql+asyncpg"
    host: str = "database"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    name: str = "family_budget"

    @property
    def url(self) -> str:
        return (
            f"{self.driver}://"
            f"{self.user}:{self.password}@"
            f"{self.host}:{self.port}/"
            f"{self.name}"
        )

    @property
    def default_database_url(self) -> str:
        """returns the url to the default database."""

        return (
            f"{self.driver}://"
            f"{self.user}:{self.password}@"
            f"{self.host}:{self.port}/"
            f"postgres"
        )


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
        env_prefix="FBB__",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    debug: bool = False
    cors: CORSSettings = CORSSettings()
    logging: LoggingSettings = LoggingSettings()
    database: DatabaseSettings = DatabaseSettings()


settings = Settings()
