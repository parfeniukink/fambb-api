"""
this module includes tests related to the user and user configuration.
"""

import asyncio

import httpx
import pytest
from fastapi import status

from src.domain import users as domain
from src.infrastructure import database


# ==================================================
# tests for not authorized
# ==================================================
async def test_user_retrieve_anonymous(anonymous):
    response: httpx.Response = await anonymous.get("/identity/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_user_update_configuration_anonymous(
    anonymous: httpx.AsyncClient,
):
    response: httpx.Response = await anonymous.patch(
        "/identity/users/configuration", json={}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_user_retrieve(john, client):
    response: httpx.Response = await client.get("/identity/users")
    result: dict = response.json()["result"]
    users_total = await domain.UserRepository().count(database.User)

    assert response.status_code == status.HTTP_200_OK
    assert result["id"] == john.id
    assert result["name"] == john.name
    assert users_total == 1


@pytest.mark.parametrize(
    "payload_id,payload",
    [
        (
            1,
            {
                "defaultCurrencyId": 1,
                "defaultCostCategoryId": 2,
            },
        ),
        (
            2,
            {
                "defaultCostCategoryId": 1,
            },
        ),
        (
            3,
            {
                "costSnippets": ["Coffee", "Water"],
                "incomeSnippets": ["Office", "Teaching"],
            },
        ),
        (
            4,
            {"showEquity": True},
        ),
        (
            5,
            {"notifyCostThreshold": 100.01},
        ),
    ],
)
@pytest.mark.use_db
async def test_user_configuration_update(
    john, client, currencies, cost_categories, payload_id, payload
):
    repository = domain.UserRepository()
    response: httpx.Response = await client.patch(
        "/identity/users/configuration", json=payload
    )
    response_user: httpx.Response = await client.get("/identity/users")
    configuration_raw_response = response_user.json()["result"][
        "configuration"
    ]

    users_total, user = await asyncio.gather(
        repository.count(database.User), repository.user_by_id(john.id)
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert users_total == 1

    if payload_id == 1:
        assert (
            user.default_currency_id
            == configuration_raw_response["defaultCurrency"]["id"]
            == payload["defaultCurrencyId"]
        )
        assert (
            user.default_cost_category_id
            == configuration_raw_response["defaultCostCategory"]["id"]
            == payload["defaultCostCategoryId"]
        )
        assert user.cost_snippets is None
        assert user.income_snippets is None
        assert (
            user.show_equity
            is configuration_raw_response["showEquity"]
            is False
        )
    elif payload_id == 2:
        assert (
            user.default_currency_id
            == configuration_raw_response["defaultCurrency"]
            is None
        )
        assert (
            user.default_cost_category_id
            == configuration_raw_response["defaultCostCategory"]["id"]
            == payload["defaultCostCategoryId"]
        )
        assert (
            user.cost_snippets
            == configuration_raw_response["costSnippets"]
            is None
        )
        assert (
            user.income_snippets
            is configuration_raw_response["incomeSnippets"]
            is None
        )
        assert (
            user.show_equity
            is configuration_raw_response["showEquity"]
            is False
        )
    elif payload_id == 3:
        assert (
            user.default_currency_id
            == configuration_raw_response["defaultCurrency"]
            is None
        )
        assert (
            user.default_cost_category_id
            == configuration_raw_response["defaultCostCategory"]
            is None
        )
        assert (
            user.cost_snippets
            == configuration_raw_response["costSnippets"]
            == ["Coffee", "Water"]
        )
        assert (
            user.income_snippets
            == configuration_raw_response["incomeSnippets"]
            == ["Office", "Teaching"]
        )
        assert (
            user.show_equity
            is configuration_raw_response["showEquity"]
            is False
        )
    elif payload_id == 4:
        assert (
            user.show_equity
            is configuration_raw_response["showEquity"]
            is True
        )
    elif payload_id == 5:
        assert user.notify_cost_threshold == 100_01
        assert configuration_raw_response["notifyCostThreshold"] == 100.01


@pytest.mark.use_db
async def test_user_update_monobank_api_key(john: domain.User, client):
    payload = {"monobankApiKey": "Test API Key"}
    response: httpx.Response = await client.patch(
        "/identity/users/configuration", json=payload
    )

    response_user: httpx.Response = await client.get("/identity/users")
    configuration_raw_response = response_user.json()["result"][
        "configuration"
    ]

    database_user: database.User = await domain.UserRepository().user_by_id(
        john.id
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert john.configuration.monobank_api_key is None

    assert (
        configuration_raw_response.get("monobankApiKeyIsSet") is True
    ), configuration_raw_response
    assert (
        configuration_raw_response.get("monobankApiKey") is None
    ), configuration_raw_response
    assert database_user.monobank_api_key == payload["monobankApiKey"]
