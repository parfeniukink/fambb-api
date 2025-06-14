# This file includes application scripts that could be used
# by developers for any purposes.

# Dependency management
# -------------------------------------------------------------------------
.PHONY: lock  # pin main dependencies
lock:
	python -m piptools compile -o requirements/main.txt
	python -m piptools compile --extra=dev -o requirements/dev.txt


.PHONY: install  # sync for dev dependencies
install:
	python -m piptools sync requirements/dev.txt


.PHONY: install.prod  # sync for prod dependencies
install.prod:
	python -m piptools sync requirements/main.txt


.PHONY: upgrade  # upgrade dependencies (generates new .txt files)
upgrade:
	python -m piptools compile --upgrade -o requirements/main.txt
	python -m piptools compile --extra dev --upgrade -o requirements/dev.txt



# Alembic migrations
# -------------------------------------------------------------------------
.PHONY: revision
revision:
	alembic revision --autogenerate


.PHONY: migrate
migrate:
	alembic upgrade head


# Infrastructure Tier
# -------------------------------------------------------------------------
.PHONY: infra
infra:
	docker compose up -d database cache


# Application Entrypoint
# -------------------------------------------------------------------------
.PHONY: run
run:
	uvicorn src.main:app --reload

.PHONY: run.prod
run.prod:
	gunicorn src.main:app --worker-class uvicorn.workers.UvicornWorker


# Tests
# -------------------------------------------------------------------------
.PHONY: test
test:
	python -m pytest -q -r p ./tests

.PHONY: test.int
test.int:
	python -m pytest ./tests/integration

.PHONY: test.unit
test.unit:
	python -m pytest ./tests/unit

.PHONY: xtest
xtest:
	python -m pytest -n 4 ./tests


# Code quality
# -------------------------------------------------------------------------
.PHONY: quality
quality:
	python -m black .
	python -m isort .


.PHONY: check
check:
	python -m flake8 .
	python -m isort --check .
	python -m black --check .
	python -m mypy --check-untyped-defs



# Application specific
# -------------------------------------------------------------------------
.PHONY: create_user
create_user:
	python -m scripts.create_user
