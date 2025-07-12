import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import asyncpg
import httpx
import pytest
import respx
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient
from loguru import logger
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import text

from src import domain, http
from src.config import settings
from src.infrastructure import Cache, database, errors, factories
from tests.mock import Cache as MockedCache


def pytest_configure() -> None:
    """allows you to configure pytest for each runtime.

    examples:
        ``PYTEST__LOGGING=off python -m pytest tests/`` - supresses
            logging output and gives only clean pytest output.
    """

    if os.getenv("PYTEST__LOGGING", "") == "off":
        # Disable logs
        logging.disable(
            logging.CRITICAL
        )  # This disables all logging below CRITICAL

        logger.disable("src.infrastructure")
        logger.disable("src.presentation")
        logger.disable("src.domain")
        logger.disable("src.operational")


# =====================================================================
# application fixtures
# =====================================================================
@pytest.fixture
def app() -> FastAPI:
    return factories.asgi_app(
        debug=settings.debug,
        rest_routers=(
            http.analytics_router,
            http.costs_router,
            http.currencies_router,
            http.exchange_router,
            http.incomes_router,
            http.notifications_router,
            http.transactions_router,
            http.users_router,
        ),
        exception_handlers={
            ValueError: errors.value_error_handler,
            RequestValidationError: errors.unprocessable_entity_error_handler,
            HTTPException: errors.fastapi_http_exception_handler,
            errors.BaseError: errors.base_error_handler,
            NotImplementedError: errors.not_implemented_error_handler,
            Exception: errors.unhandled_error_handler,
        },
    )


@pytest.fixture
async def john() -> domain.users.User:
    """create default user 'John' for tests."""

    async with database.transaction() as session:
        user = await domain.users.UserRepository().add_user(
            candidate=database.User(
                name="john", token="41d917c7-464f-4056-b2de-1a6e2fbfd9e7"
            )
        )
        await session.flush()  # get user id

    return domain.users.User.from_instance(user)


@pytest.fixture
async def marry() -> domain.users.User:
    """create default user 'Marry' for tests."""

    async with database.transaction() as session:
        user = await domain.users.UserRepository().add_user(
            candidate=database.User(
                name="marry", token="fda4b8f6-4bf3-43e2-b3a2-7c3905ee0af1"
            )
        )
        await session.flush()  # get user id

    return domain.users.User.from_instance(user)


@pytest.fixture
async def anonymous(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Returns the client without the authorized user."""

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def client(
    app: FastAPI, john: domain.users.User
) -> AsyncGenerator[AsyncClient, None]:
    """return the default 'John' authorized client"""

    headers = {"Authorization": f"Bearer {john.token}"}

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers=headers,
    ) as client:

        yield client


@pytest.fixture
async def client_marry(
    app: FastAPI, marry: domain.users.User
) -> AsyncGenerator[AsyncClient, None]:
    """return authorized client 'Marry'"""

    headers = {"Authorization": f"Bearer {marry.token}"}

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers=headers,
    ) as client:
        yield client


# =====================================================================
# DATABASE SECTION
# =====================================================================
@pytest.yield_fixture(scope="session")
def event_loop():
    """fix a lot of shit..."""

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _auto_patch_database_name(session_mocker) -> None:
    """adjust the database name.

    notes:
        if the xdist package is used the database name will be updated with
        the worker ``id`` that comes from the ``PYTEST_XDIST_WORKER`` env.
    """

    xdist_worker_name: str = os.getenv("PYTEST_XDIST_WORKER", "main")
    session_mocker.patch(
        "src.config.settings.database.name",
        f"family_budget_test_{xdist_worker_name}",
    )


@pytest.fixture(scope="session", autouse=True)
async def test_database_engine(
    _auto_patch_database_name,
) -> AsyncGenerator[AsyncEngine, None]:
    """create the test database if not exists and then drop it.
    the database test name is overridden in pyproject.toml.

    worker id comes from the pytest-xdist. this about creating temporary
    databases base on the worker id information in order to make
    testing more efficient.
    """

    test_database_engine: AsyncEngine = create_async_engine(
        settings.database.url,
        poolclass=NullPool,
    )
    default_database_engine: AsyncEngine = create_async_engine(
        settings.database.default_database_url,
        poolclass=NullPool,
    )

    try:
        # Try to connect to the test database
        async with test_database_engine.connect() as conn:
            await conn.close()
    except asyncpg.exceptions.InvalidCatalogNameError:
        # Connect to the default database and create the test database
        async with default_database_engine.connect() as conn:
            # https://docs.sqlalchemy.org/en/20/core/connections.html#setting-transaction-isolation-levels-including-dbapi-autocommit  # noqa: E501
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(
                text(f"CREATE DATABASE {settings.database.name}")
            )
            await conn.execute(text("COMMIT"))

    except ConnectionRefusedError:
        raise SystemExit(
            "Database connection refused. "
            "Please check if the database is running."
        )

    await default_database_engine.dispose()

    yield test_database_engine

    async with default_database_engine.connect() as conn:
        # Revoke connect privileges from all users
        await conn.execute(
            text(
                f"REVOKE CONNECT ON DATABASE "
                f"{settings.database.name} FROM PUBLIC"
            )
        )


# =====================================================================
# CACHE SECTION
# =====================================================================
@pytest.fixture(autouse=True)
def patch_cache_service(mocker) -> MagicMock:
    """This fixture patches the cache service to use the in-memory
    cache repository.
    """

    return mocker.patch.object(Cache, "__new__", return_value=MockedCache())


@pytest.fixture(autouse=True)
def _mock_httpx_requests():
    with respx.mock(assert_all_mocked=True):
        yield


# ==================================================
# MARKERS
# ==================================================
@pytest.fixture(autouse=True)
async def _db_marker(request, test_database_engine):
    """this fixture automatically creates and cleans database tables.

    USAGE
        >>> @pytest.mark.use_db
        >>> async def test_a():
        >>>     # some database interaction

    """

    if request.node.get_closest_marker("use_db") is None:
        yield
    else:
        async with test_database_engine.connect() as conn:
            await conn.run_sync(database.Base.metadata.drop_all)
            await conn.run_sync(database.Base.metadata.create_all)
            await conn.execute(text("COMMIT"))

        yield

        await test_database_engine.dispose()
