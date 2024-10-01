"""
this package includes high-level tests for cost operatinos
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
    response = await anonymous.get("/costs/categories")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_cost_categories_create_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.post("/costs/categories", json={"name": "..."})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_cost_categories_fetch(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.get("/costs/categories")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["result"]) == len(cost_categories)


@pytest.mark.use_db
async def test_cost_category_creation(
    client: httpx.AsyncClient, cost_categories
):
    response = await client.post(
        "/costs/categories", json={"name": "Another yet category"}
    )

    total = await domain.transactions.TransactionRepository().count(
        database.CostCategory
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert total == len(cost_categories) + 1


@pytest.mark.use_db
async def test_costs_fetch(client: httpx.AsyncClient, cost_factory):
    """test response paginated by default."""

    costs: list[database.Cost] = await cost_factory(n=15)

    response1: httpx.Response = await client.get("/costs")
    response1_data = response1.json()
    response2: httpx.Response = await client.get(
        "/costs", params={"context": response1_data["context"]}
    )
    response2_data = response2.json()

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    assert total == len(costs)
    assert response1.status_code == status.HTTP_200_OK
    assert len(response1_data["result"]) == 10
    assert response1_data["context"] == 10
    assert response1_data["left"] == 5
    assert len(response2_data["result"]) == 5
    assert response2_data["context"] == 15
    assert response2_data["left"] == 0


@pytest.mark.use_db
async def test_cost_add(
    client: httpx.AsyncClient, cost_categories, currencies
):
    response = await client.post(
        "/costs",
        json={
            "name": "PS5",
            "value": 100,
            "timestamp": "2024-09-28",
            "currency_id": 1,
            "category_id": 1,
        },
    )

    total = await domain.transactions.TransactionRepository().count(
        database.Cost
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=1)
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total == 1
    assert currency.equity == currencies[0].equity - 100


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
