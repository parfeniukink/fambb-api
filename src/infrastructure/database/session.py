import functools
from collections.abc import Callable
from contextvars import ContextVar

from sqlalchemy import Query, Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

CTX_SESSION: ContextVar[AsyncSession | None] = ContextVar(
    "session", default=None
)

async_engine_factory: Callable[[str], AsyncEngine] = functools.partial(
    create_async_engine, pool_pre_ping=True
)


@functools.lru_cache(maxsize=1)
def create_engine() -> AsyncEngine:
    """Create a new async database engine.
    A function result is cached since there is not reason to
    initiate the engine more than once since session is created
    for each separate transaction if needed.
    """

    # TODO: Replace with settings.database.url

    return async_engine_factory("sqlite://db.sqlite3")


def create_session(engine: AsyncEngine | None = None) -> AsyncSession:
    """Creates a new async session to execute SQL queries."""

    return AsyncSession(
        engine or create_engine(), expire_on_commit=True, autoflush=False
    )


class Session:
    """The basic class to perfoem database operations within the session."""

    # All sqlalchemy errors that can be raised
    _ERRORS = (IntegrityError, InvalidRequestError)

    def __init__(self) -> None:
        if (_session := CTX_SESSION.get()) is not None:
            self._session: AsyncSession = _session
        else:
            self._session = create_session()
            CTX_SESSION.set(self._session)

    async def execute(self, query: Query) -> Result:
        try:
            result: Result = await self._session.execute(query)
            return result
        except self._ERRORS as error:
            raise Exception(error) from error
