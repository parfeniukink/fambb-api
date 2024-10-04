"""
test analytics.
"""

import httpx
import pytest
from fastapi import status


# ==================================================
# tests for not authorized
# ==================================================
async def test_transactions_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/analytics/transactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_transactions_fetch(
    client: httpx.AsyncClient, cost_factory, income_factory, exchange_factory
):
    await cost_factory(n=10)
    await income_factory(n=10)
    await exchange_factory(n=10)

    response1: httpx.Response = await client.get("/analytics/transactions")
    response1_data = response1.json()
    response2: httpx.Response = await client.get(
        "/analytics/transactions",
        params={"context": response1_data["context"]},
    )
    response2_data = response2.json()
    response3: httpx.Response = await client.get(
        "/analytics/transactions",
        params={"context": response2_data["context"]},
    )
    response3_data = response3.json()
    response4: httpx.Response = await client.get(
        "/analytics/transactions",
        params={"context": response3_data["context"]},
    )
    response4_data = response4.json()

    assert response1.status_code == status.HTTP_200_OK, response1.json()
    assert response2.status_code == status.HTTP_200_OK, response2.json()
    assert response3.status_code == status.HTTP_200_OK, response2.json()
    assert response4.status_code == status.HTTP_200_OK, response2.json()
    assert len(response1_data["result"]) == 10
    assert len(response2_data["result"]) == 10
    assert len(response3_data["result"]) == 10
    assert len(response4_data["result"]) == 0
    assert response1_data["context"] == 10
    assert response2_data["context"] == 20
    assert response3_data["context"] == 30
    assert response1_data["left"] == 20
    assert response2_data["left"] == 10
    assert response3_data["left"] == 0
