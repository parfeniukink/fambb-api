"""
this package is about Command & Query Separation. there is no real reason
to separate commands and queries on the operational layer.

since, the 'Repository' pattern is used as a high-level data access layer,
there is only the reason to separate queries from database mutation.

the main reason to have it is 'async' way. the ``Command`` logical component
requires the transaction, when the ``Query`` allows to request for the
data concurrently.

IMPORTANT: the CQS is a lowes level to access the data from the database.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure import errors

from .session import engine_factory, session_factoy

CTX_CQS_COMMAND_SESSION: ContextVar[AsyncSession | None] = ContextVar(
    "cqs command session", default=None
)


@asynccontextmanager
async def transaction():
    session: AsyncSession = session_factoy()
    CTX_CQS_COMMAND_SESSION.set(session)

    try:
        async with session.begin():
            yield session
    except errors.NotFoundError as error:
        logger.error(error)
        raise error
    except Exception as error:
        logger.error(error)
        raise errors.DatabaseError(str(error)) from error
    finally:
        # clean the connections pool
        await engine_factory().dispose()


class Command:
    """cqs 'Command' non-data descriptor

    usage:
        ```py
        async with self.query.session as session:
            async with session.begin():
                result: Result = await session.execute(
                    select(database.Table)
                )
                return tuple(result.scalars().all())
        ```
    """

    def __get__(self, instance, owner):
        if not (session := CTX_CQS_COMMAND_SESSION.get()):
            raise ValueError(
                "Transaction is not set. Use `async with transaction()`"
            )
        else:
            setattr(self, "_session", session)
            return self

    @property
    def session(self) -> AsyncSession:
        try:
            return getattr(self, "_session")
        except AttributeError:
            raise ValueError("There is no _session object for the Command")


class Query:
    def __get__(self, instance, owner):
        return self

    @property
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """create a new session for each new query to be able to get them concurrently."""

        session = session_factoy()

        try:
            yield session
        except AttributeError:
            raise ValueError("There is no _session object for the Query")
        except errors.NotFoundError as error:
            logger.error(error)
            raise error
        except Exception as error:
            logger.error(error)
            raise errors.DatabaseError(str(error)) from error
        finally:
            await session.close()
