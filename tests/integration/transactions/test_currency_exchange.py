"""
this package includes high-level tests for currency exchange operatinos
"""

import asyncio

import httpx
import pytest
from fastapi import status

from src import domain
from src.infrastructure import database


# ==================================================
# tests for not authorized
# ==================================================
async def test_exchange_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/exchange")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_exchange_add_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post("/exchange", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_exchange_fetch(client: httpx.AsyncClient, exchange_factory):
    """test response paginated by default."""

    items: list[database.Exchange] = await exchange_factory(n=15)

    response1: httpx.Response = await client.get("/exchange")
    response1_data = response1.json()

    response2: httpx.Response = await client.get(
        "/exchange", params={"context": response1_data["context"]}
    )
    response2_data = response2.json()

    total = await domain.transactions.TransactionRepository().count(
        database.Exchange
    )

    assert total == len(items)

    assert response1.status_code == status.HTTP_200_OK
    assert len(response1_data["result"]) == 10
    assert response1_data["context"] == 10
    assert response1_data["left"] == 5

    assert len(response2_data["result"]) == 5
    assert response2_data["context"] == 15
    assert response2_data["left"] == 0


@pytest.mark.use_db
async def test_exchange_add(client: httpx.AsyncClient, currencies):
    response = await client.post(
        "/exchange",
        json={
            "fromCurrencyId": 1,
            "fromValue": 100,
            "toCurrencyId": 2,
            "toValue": 2000,
        },
    )

    total = await domain.transactions.TransactionRepository().count(
        database.Exchange
    )

    tasks = (
        domain.equity.EquityRepository().currency(id_=1),
        domain.equity.EquityRepository().currency(id_=2),
    )

    from_currency, to_currency = await asyncio.gather(*tasks)

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total == 1
    assert from_currency.equity == currencies[0].equity - 100
    assert to_currency.equity == currencies[1].equity + 2000


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
async def test_exchange_add_unprocessable(
    client: httpx.AsyncClient, payload: dict
):
    response = await client.post("/exchange", json=payload)

    total = await domain.transactions.TransactionRepository().count(
        database.Exchange
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert total == 0
