import logging
import os
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import httpx
import psycopg2
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


@pytest.hookimpl
def pytest_sessionstart(session):
    worker = os.getenv("PYTEST_XDIST_WORKER", "main")
    settings.database.name = f"family_budget_test_{worker}"

    # Ensure DB Exists
    conn = psycopg2.connect(settings.database.default_database_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname=%s", (settings.database.name,)
    )

    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{settings.database.name}"')
        print(f"Database {settings.database.name} is created")

    cur.close()
    conn.close()


@pytest.fixture(autouse=True)
async def reset_database(request):
    """
    USAGE

        @pytest.mark.use_db
        async def test_foo():
            assert ...

    NOTES

    in the `pyproject.toml` file next settings must be specified:
        - asyncio_default_fixture_loop_scope = "session"
        - asyncio_default_test_loop_scope = "session"

    it ensures that we use

    """

    if request.node.get_closest_marker("use_db"):
        engine: AsyncEngine = create_async_engine(
            settings.database.url, echo=False, poolclass=NullPool
        )

        async with engine.begin() as conn:
            await conn.run_sync(database.Base.metadata.drop_all)
            await conn.run_sync(database.Base.metadata.create_all)
            await conn.execute(text("COMMIT"))


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

    repo = domain.users.UserRepository()

    async with database.transaction():
        candidate: database.User = await repo.add_user(
            candidate=database.User(
                name="john", token="41d917c7-464f-4056-b2de-1a6e2fbfd9e7"
            )
        )

    user: database.User = await repo.user_by_id(candidate.id)

    return domain.users.User.from_instance(user)


@pytest.fixture
async def marry() -> domain.users.User:
    """create default user 'Marry' for tests."""

    repo = domain.users.UserRepository()

    async with database.transaction():
        candidate: database.User = await repo.add_user(
            candidate=database.User(
                name="marry", token="fda4b8f6-4bf3-43e2-b3a2-7c3905ee0af1"
            )
        )

    user: database.User = await repo.user_by_id(candidate.id)

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
