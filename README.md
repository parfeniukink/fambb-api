# REASONING

I need a REST API to manage user settings, shared finances (transactions), observe analytics using [this frontend client](https://github.com/parfeniukink/fambb-frontend)

---

# ARCHITECTURE

**INFRASTRUCTURE:** python http application, relational database, cache
**REASONING:** I know Python, I need a good DB transactions engine, all systems need cache
**APPRACHES:** monolith, REST, DDD, CQS, Repository, asynchronous
**TOOLS:** `FastAPI`, `PostgreSQL`, `memcached`

---

# BACKLOG

- settings
  - number of `last transactions`
  - exclude `categories` from costs calculations
- authorization
  - if user credentials are not valid - return the WWW-Authorization HTTP header with detaild according to the RFC6750
  - use JWT for security

# DEV SETUP

1. project python tools configurations: `pyproject.toml`, `.flake8`
2. dependencies are managed with `pip-tools`
3. useful dev scripts are in the `Makefile`, use `make` command
4. tests: `tests/integration`, `tests/unit`
5. tests are fully powered by `pytest`
6. code quality: only linter and chekcer in CI, use `make check` and `make quality` locally
7. CI/CD: github actions

## COMMANDS

```shell
# LOCAL
# activate
virtualenv --python python3 venv
source venv/bin/activate

pip insatll pip-tools
make install



# PRODUCTION
virtualenv --python python3 venv
source venv/bin/activate
pip install -r requirements/main.txt
```
