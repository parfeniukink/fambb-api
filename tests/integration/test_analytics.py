"""
test analytics.
"""

import asyncio
from datetime import date, timedelta

import httpx
import pytest
from fastapi import status

from src import domain
from src.infrastructure import database
from tests.integration.conftest import (
    CostCandidateFactory,
    ExchangeCandidateFactory,
    IncomeCandidateFactory,
)


# ==================================================
# tests for not authorized
# ==================================================
async def test_transactions_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/analytics/transactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_transaction_basic_analytics_fetch_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.get("/analytics/basic")
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
    assert response3_data["left"] == 0


@pytest.mark.use_db
async def test_basic_analytics_fetch(
    john: domain.users.User,
    client: httpx.AsyncClient,
    currencies,
    cost_categories,
):
    """
    create different transactions and check the response
    for expected results.

    EXAMPLE OF EXCHANGE TRANSACTION
    1. 100.000 UAH -> 200.000 USD
    2. 50.000 USD -> 25.000 UAH
    3. 100.000 UAH -> 200.000 USD

    CALCULATION FOR EXCHANGE TRANSACTIONS
    UAH: -200.000 + 25.000 = -175.000 (exclude from calculation)
    USD: +400.000 - 50.000 = +350.000 (include in calculation)
    """

    first_currency, second_currency = currencies
    food_category, other_category = cost_categories
    today: date = date.today()
    yesterday: date = today - timedelta(days=1)
    far_ago: date = yesterday - timedelta(days=10)

    # prepare data
    cost_candidates: tuple[database.Cost, ...] = (
        CostCandidateFactory.build(
            user_id=john.id,
            currency_id=second_currency.id,  # should be skipped
            category_id=food_category.id,
            value=200_00,
            timestamp=today,
        ),
        CostCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            category_id=food_category.id,
            value=50_00,
            timestamp=far_ago,  # should be skipped
        ),
        CostCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            category_id=food_category.id,
            value=100_00,
            timestamp=today,
        ),
        CostCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            category_id=other_category.id,
            value=100_00,
            timestamp=yesterday,
        ),
    )

    income_candidates: tuple[database.Income, ...] = (
        IncomeCandidateFactory.build(
            user_id=john.id,
            currency_id=second_currency.id,  # should be skipped
            source="revenue",
            value=500_00,
            timestamp=today,
        ),
        IncomeCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            source="revenue",
            value=200_00,
            timestamp=today,
        ),
        IncomeCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            source="revenue",
            value=100_00,
            timestamp=yesterday,
        ),
        IncomeCandidateFactory.build(
            user_id=john.id,
            currency_id=first_currency.id,
            source="revenue",
            value=50_00,
            timestamp=far_ago,  # should be skipped
        ),
    )

    exchange_candidates: tuple[database.Exchange, ...] = (
        ExchangeCandidateFactory.build(
            user_id=john.id,
            from_currency_id=second_currency.id,
            to_currency_id=first_currency.id,
            from_value=100_00,
            to_value=200_00,
            timestamp=today,
        ),
        ExchangeCandidateFactory.build(
            user_id=john.id,
            from_currency_id=first_currency.id,
            to_currency_id=second_currency.id,
            from_value=50_00,  # skip for FIRST CURRENCY
            to_value=25_00,
            timestamp=yesterday,
        ),
        ExchangeCandidateFactory.build(
            user_id=john.id,
            from_currency_id=second_currency.id,
            to_currency_id=first_currency.id,
            from_value=100_00,
            to_value=200_00,
            timestamp=yesterday,
        ),
    )
    async with database.transaction() as session:
        cost_create_tasks = (
            domain.transactions.TransactionRepository().add_cost(candidate)
            for candidate in cost_candidates
        )
        income_create_tasks = (
            domain.transactions.TransactionRepository().add_income(candidate)
            for candidate in income_candidates
        )
        exchange_create_tasks = (
            domain.transactions.TransactionRepository().add_exchange(candidate)
            for candidate in exchange_candidates
        )

        await asyncio.gather(
            *cost_create_tasks, *income_create_tasks, *exchange_create_tasks
        )
        await session.flush()

    # perform the request
    response: httpx.Response = await client.get(
        "/analytics/basic",
        params={
            "startDate": yesterday.strftime("%Y-%m-%d"),
            "endDate": today.strftime("%Y-%m-%d"),
        },
    )

    raw_response: dict = response.json()

    assert response.status_code == status.HTTP_200_OK, raw_response
    assert raw_response == {
        "result": [
            {
                "costs": {
                    "categories": [
                        {"name": "Food", "total": 200.00, "ratio": 100.0},
                    ],
                    "total": 200.00,
                },
                "totalRatio": 40,
                "currency": {"id": 2, "name": "FOO", "sign": "#"},
                "incomes": {
                    "sources": [
                        {"source": "revenue", "total": 500.00},
                    ],
                    "total": 500.00,
                },
                "fromExchanges": -175.0,
            },
            {
                "costs": {
                    "categories": [
                        {"name": "Food", "total": 100.00, "ratio": 50.0},
                        {"name": "Other", "total": 100.00, "ratio": 50.0},
                    ],
                    "total": 200.00,
                },
                "totalRatio": 30.8,
                "currency": {"id": 1, "name": "USD", "sign": "$"},
                "incomes": {
                    "sources": [{"source": "revenue", "total": 300.00}],
                    "total": 300.00,
                },
                "fromExchanges": 350.0,
            },
        ],
    }
