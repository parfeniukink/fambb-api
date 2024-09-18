from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.exc import InterfaceError
from sqlalchemy.ext.asyncio import AsyncSession

from .session import CTX_SESSION, create_session


@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    """Use this context manager to perform database transactions
    in any coroutine in the source code.
    """

    session: AsyncSession = create_session()
    CTX_SESSION.set(session)

    try:
        yield session
        await session.commit()
    except Exception as error:
        # NOTE: If any sort of issues are occurred in the code
        #       they are handled on the BaseCRUD level and raised
        #       as a DatabseError.
        #       If the DatabseError is handled within domain/application
        #       levels it is possible that `await session.commit()`
        #       would raise an error.
        logger.error(f"Rolling back changes. {error}")
        await session.rollback()
        raise error from error
    finally:
        try:
            await session.close()
        except InterfaceError as error:
            logger.error(f"Close session error: {error}")


def atomic(coro):
    """Just a decorator implementation of `transaction` context manager."""

    @wraps(coro)
    async def inner(*args, **kwargs):
        async with transaction():
            return await coro(*args, **kwargs)

    return inner
