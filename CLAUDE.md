# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Family Budget Bot - a REST API for managing shared family finances (transactions, analytics) built with FastAPI, PostgreSQL, and memcached. Uses DDD-inspired architecture with CQS (Command Query Separation) pattern for async database operations.

## Commands

```bash
# Dependencies (pip-tools)
make install          # sync dev dependencies
make lock             # pin dependencies to requirements/*.txt
make upgrade          # upgrade all dependencies

# Run application
make infra            # start database and cache containers
make run              # dev server (uvicorn --reload on port 8001)
make migrate          # run alembic migrations

# Testing
make test             # run all tests
make xtest            # run tests in parallel (4 workers)
python -m pytest tests/path/to/test_file.py::test_function  # single test

# Code quality
make fix              # format with black + isort
make check            # lint (flake8, isort, black, mypy)
```

## Architecture

```
src/
├── main.py           # FastAPI app entrypoint
├── http/             # Presentation tier
│   ├── resources/    # API endpoints (routers)
│   └── contracts/    # Request/response Pydantic schemas
├── operational/      # Application tier (use cases, orchestration)
├── domain/           # Business model tier
│   ├── transactions/ # Costs, Incomes, Exchanges, CostShortcuts
│   ├── equity/       # Currency and equity management
│   ├── users/        # User entities and repository
│   └── notifications/
├── infrastructure/   # Infrastructure tier
│   └── database/
│       ├── tables.py     # SQLAlchemy ORM models
│       ├── cqs.py        # Command/Query separation (transaction context)
│       └── repository.py # Base repository with pagination
└── integrations/     # External services (monobank)
```

### Key Patterns

**CQS (Command Query Separation)**: Database writes require `async with database.transaction()` context. Queries can run concurrently outside transactions.

```python
# Write operation - requires transaction
async with database.transaction() as session:
    item = await repository.add_cost(candidate)
    await session.flush()

# Read operation - no transaction needed
items = await repository.costs(user_id=1, offset=0, limit=10)
```

**Repository Pattern**: Domain repositories in `src/domain/*/repository.py` extend `src.infrastructure.database.Repository` base class.

**Data Flow**: HTTP Resources → Operational (orchestration) → Domain (repositories) → Infrastructure (database)

## Configuration

Environment variables prefixed with `FBB__` (nested: `FBB__DATABASE__HOST`). See `src/config/__init__.py` for all settings.

## Testing

- Tests require running database (`make infra`)
- Use `@pytest.mark.use_db` marker for tests that interact with database
- Fixtures: `john`, `marry` (users), `client` (authorized httpx client), `anonymous` (unauthorized client)
- Factory fixtures: `cost_factory`, `income_factory`, `exchange_factory`, `cost_shortcut_factory`
- pytest-xdist creates isolated test databases per worker
- Suppress logs in tests: `FBB__PYTEST_LOGGING=off`

## Code Style

- Line length: 79 characters
- Python 3.12+
- Type hints required (mypy with pydantic and sqlalchemy plugins)
- `InternalData` base class for domain entities (Pydantic with `from_attributes=True`)
