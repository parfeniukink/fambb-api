"""
this package includes high-level tests for Cost operatinos
"""

import httpx
import pytest
from fastapi import status

from src import domain
from src.infrastructure import database


# ==================================================
# tests for not authorized
# ==================================================
async def test_cost_categories_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("costs/categories")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_cost_categories_create_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.post("costs/categories", json={"name": "..."})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_cost_categories_fetch(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.get("costs/categories")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["result"]) == len(cost_categories)


@pytest.mark.use_db
async def test_cost_category_creation(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.post(
        "costs/categories", json={"name": "Another yet category"}
    )

    total = await domain.transactions.TransactionRepository().count(
        database.CostCategory
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert total == len(cost_categories) + 1


# ==================================================
# tests for validation
# ==================================================
@pytest.mark.parametrize(
    "payload,error_type",
    [
        ({}, "missing"),
        ({"name": None}, "bad-type"),
        ({"name": 12}, "bad-type"),
        ({"another-field": "proper string"}, "missing"),
    ],
)
@pytest.mark.use_db
async def test_cost_category_creation_unprocessable(
    client: httpx.AsyncClient, payload, error_type
):
    response = await client.post("costs/categories", json=payload)

    total = await domain.transactions.TransactionRepository().count(
        database.CostCategory
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        response.json()["result"][0]["detail"]["type"] == error_type
    ), response.json()
    assert total == 0
