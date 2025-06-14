from datetime import date, timedelta
from typing import Final

import httpx
import pytest
from fastapi import status

from src.infrastructure import database


async def test_transactions_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/transactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.use_db
async def test_transactions_fetch(
    client: httpx.AsyncClient, cost_factory, income_factory, exchange_factory
):
    await cost_factory(n=10)
    await income_factory(n=10)
    await exchange_factory(n=10)

    response1: httpx.Response = await client.get("/transactions")
    response1_data = response1.json()
    response2: httpx.Response = await client.get(
        "/transactions",
        params={"context": response1_data["context"]},
    )

    response2_data = response2.json()
    response3: httpx.Response = await client.get(
        "/transactions",
        params={"context": response2_data["context"]},
    )
    response3_data = response3.json()
    response4: httpx.Response = await client.get(
        "/transactions",
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
    assert response3_data["left"] == 0


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_dates_and_category(
    client: httpx.AsyncClient,
    today: date,
    DATE_FORMAT: str,
    cost_factory,
    income_factory,
    cost_categories: list[database.CostCategory],
):
    """
    1. create costs with 'too far' creation date
    2. create 'last made' costs
    3. fetch with filters to exclude 'too far' costs

    NOTES
    by default (in pytest fixture) the first item is used (where index=0)

    """

    await cost_factory(n=10, timestamp=today - timedelta(days=100))
    await cost_factory(n=10, timestamp=today - timedelta(days=30))
    await income_factory(n=5, timestamp=today - timedelta(days=30))

    # define query strings
    start_date_qs: Final = (today - timedelta(days=40)).strftime(DATE_FORMAT)
    end_date_qs: Final = today.strftime(DATE_FORMAT)

    url = (
        "/transactions?"
        f"startDate={start_date_qs}&"
        f"endDate={end_date_qs}&"
        f"category={cost_categories[0].id}"
    )

    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    assert len(response_data["result"]) == 10, response_data
    assert response_data["left"] == 5, response_data


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_period_and_operation(
    client: httpx.AsyncClient, today: date, cost_factory, income_factory
):
    await cost_factory(n=10, timestamp=today - timedelta(days=100))
    await cost_factory(n=10, timestamp=today)
    await income_factory(n=5, timestamp=today)

    url = "/transactions?period=current-month&operation=income"
    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    assert len(response_data["result"]) == 5, response_data
    assert response_data["left"] == 0, response_data
