"""
test equity and currencies.
"""

import httpx
import pytest
from fastapi import status

from src import contracts
from src.domain import equity as domain
from src.infrastructure import database


@pytest.mark.use_db
async def test_currencies_list(
    client: httpx.AsyncClient, currencies: list[database.Currency]
):
    response: httpx.Response = await client.get("/currencies")

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()["result"]) == len(currencies)


@pytest.mark.use_db
async def test_currency_creation(client: httpx.AsyncClient):
    payload = contracts.CurrencyCreateBody(name="USD", sign="$").dict()
    response: httpx.Response = await client.post("/currencies", json=payload)

    total_currencies: int = await domain.EquityRepository().count(
        database.Currency
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total_currencies == 1
