"""
this file is a part of infrastructure tier of the application.
it is base on pydantic_settings engine to make it easy to work
with environment variables (including ``.env`` file support).

HOW TO WORK WITH SETTIGNS?
1. focus on ``Settings`` class
2. if you would like to change the ``debug`` parameter go to the ``.env``
    file and add ``FBB__DEBUG``, since there is a prefix specified in
    ``model_config`` of that class
3. if you would like to change the nested parameter - use next prfix as well:
    ``FBB__DATABASE__NAME`` respectively
"""

__all__ = ("settings",)

from pydantic import BaseModel
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


class CacheSettings(BaseModel):
    host: str = "cache"
    port: int = 11211
    pool: int = 2


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
    logging: LoggingSettings = LoggingSettings()
    database: DatabaseSettings = DatabaseSettings()
    cache: CacheSettings = CacheSettings()


settings = Settings()
