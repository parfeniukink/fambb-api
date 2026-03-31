from datetime import date, timedelta
from typing import Final

import httpx
import pytest
from fastapi import status

from src.infrastructure import database


@pytest.mark.use_db
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


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_pattern_income(
    client: httpx.AsyncClient,
    today: date,
    cost_factory,
    income_factory,
):
    """Pattern filter should match income names when operation=income.

    Uses a non-matching pattern to verify the filter is actually applied.
    Without the bug fix, the pattern filter is dead code for incomes,
    so all 5 incomes would be returned even with a non-matching pattern.
    """

    await cost_factory(n=3, timestamp=today)
    await income_factory(n=5, timestamp=today)

    # Use a pattern that does NOT match "test_income"
    url = "/transactions?operation=income&pattern=nonexistent"
    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    assert len(response_data["result"]) == 0, response_data

    # Positive match: pattern that matches income names should return results
    url_match = "/transactions?operation=income&pattern=test_income"
    response_match: httpx.Response = await client.get(url_match)
    response_match_data: dict = response_match.json()

    assert (
        response_match.status_code == status.HTTP_200_OK
    ), response_match_data
    assert len(response_match_data["result"]) == 5, response_match_data


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_min_value(
    client: httpx.AsyncClient,
    today: date,
    cost_factory,
    income_factory,
):
    """minValue filter should exclude transactions below the threshold."""

    # Create costs: 3 small (500 cents = 5.00)
    # and 2 large (50000 cents = 500.00)
    await cost_factory(n=3, timestamp=today, value=500)
    await cost_factory(n=2, timestamp=today, value=50000)
    # Create incomes: 2 small and 3 large
    await income_factory(n=2, timestamp=today, value=500)
    await income_factory(n=3, timestamp=today, value=50000)

    # Filter for transactions >= 100.00 (10000 cents)
    url = "/transactions?minValue=100"
    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    # Should return 2 large costs + 3 large incomes = 5
    assert len(response_data["result"]) == 5, response_data


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_min_value_and_operation(
    client: httpx.AsyncClient,
    today: date,
    cost_factory,
    income_factory,
):
    """minValue combined with operation should filter both dimensions."""

    await cost_factory(n=3, timestamp=today, value=500)
    await cost_factory(n=2, timestamp=today, value=50000)
    await income_factory(n=5, timestamp=today, value=50000)

    # Filter for costs >= 100.00
    url = "/transactions?minValue=100&operation=cost"
    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    assert len(response_data["result"]) == 2, response_data
    assert all(item["operation"] == "cost" for item in response_data["result"])


@pytest.mark.use_db
async def test_transactions_fetch_filter_by_min_value_and_exchange(
    client: httpx.AsyncClient,
    today: date,
    exchange_factory,
):
    """minValue filter should apply to exchanges using from_value."""

    await exchange_factory(n=5)

    # Use minValue=0.01 to include all exchanges (from_value is always > 0)
    url = "/transactions?minValue=0.01&operation=exchange"
    response: httpx.Response = await client.get(url)
    response_data: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, response_data
    assert len(response_data["result"]) == 5, response_data
    assert all(
        item["operation"] == "exchange" for item in response_data["result"]
    )
