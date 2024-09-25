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


# Application entrypoint
# -------------------------------------------------------------------------
.PHONY: run
run:
	uvicorn src.main:app --reload-dir="src"



# Tests
# -------------------------------------------------------------------------
.PHONY: test
test:
	python -m pytest ./tests


# Code quality
# -------------------------------------------------------------------------
.PHONY: quality
quality:
	python -m black .
	python -m isort .


.PHONY: check
check:
	python -m isort --check .
	python -m black --check .
	python -m mypy --check-untyped-defs



# Application specific
# -------------------------------------------------------------------------
.PHONY: create_user
create_user:
	python -m scripts.create_user
