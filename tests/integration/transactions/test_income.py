"""
this package includes high-level tests for income operatinos
"""

import httpx
import pytest
from fastapi import status

from src import domain
from src.infrastructure import database, responses


# ==================================================
# tests for not authorized
# ==================================================
async def test_income_categories_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/incomes")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_income_categories_create_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post("/incomes", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_incomes_fetch(client: httpx.AsyncClient, income_factory):
    """test response paginated by default."""

    incomes: list[database.Income] = await income_factory(n=15)

    response1: httpx.Response = await client.get("/incomes")
    response1_data = response1.json()
    response2: httpx.Response = await client.get(
        "/incomes", params={"context": response1_data["context"]}
    )
    response2_data = response2.json()

    total = await domain.transactions.TransactionRepository().count(
        database.Income
    )

    assert total == len(incomes)

    assert response1.status_code == status.HTTP_200_OK
    assert len(response1_data["result"]) == 10
    assert response1_data["context"] == 10
    assert response1_data["left"] == 5

    assert len(response2_data["result"]) == 5
    assert response2_data["context"] == 15
    assert response2_data["left"] == 0


@pytest.mark.use_db
async def test_income_add(client: httpx.AsyncClient, currencies):
    response = await client.post(
        "/incomes",
        json={
            "name": "PS5",
            "value": 100,
            "source": "revenue",
            "timestamp": "2024-09-28",
            "currency_id": 1,
        },
    )

    total = await domain.transactions.TransactionRepository().count(
        database.Income
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=1)
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total == 1
    assert currency.equity == currencies[0].equity + 100


# ==================================================
# tests for validation
# ==================================================
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"name": 12},
        {"another-field": "proper string"},
    ],
)
@pytest.mark.use_db
async def test_income_add_unprocessable(
    client: httpx.AsyncClient, payload: dict
):
    response = await client.post("/incomes", json=payload)

    total = await domain.transactions.TransactionRepository().count(
        database.Income
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert total == 0
