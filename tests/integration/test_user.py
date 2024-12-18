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
    response: httpx.Response = await anonymous.get("/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_user_update_configuration_anonymous(
    anonymous: httpx.AsyncClient,
):
    response: httpx.Response = await anonymous.patch(
        "/users/configuration", json={}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
async def test_user_retrieve(john, client):
    response: httpx.Response = await client.get("/users")
    result: dict = response.json()["result"]
    users_total = await domain.UserRepository().count(database.User)

    assert response.status_code == status.HTTP_200_OK
    assert result["id"] == john.id
    assert result["name"] == john.name
    assert users_total == 1


@pytest.mark.parametrize(
    "payload",
    [
        {
            "defaultCurrencyId": 1,
            "defaultCostCategoryId": 2,
        },
        {
            "defaultCurrencyId": None,
            "defaultCostCategoryId": 1,
        },
        {
            "defaultCurrencyId": None,
            "defaultCostCategoryId": None,
        },
    ],
)
@pytest.mark.use_db
async def test_user_configuration_update(
    john,
    client,
    currencies,
    cost_categories,
    payload,
):
    repository = domain.UserRepository()
    response: httpx.Response = await client.patch(
        "/users/configuration",
        json=payload,
    )
    response_user: httpx.Response = await client.get("/users")
    configuration_raw_response = response_user.json()["result"][
        "configuration"
    ]

    users_total, user = await asyncio.gather(
        repository.count(database.User), repository.user_by_id(john.id)
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert users_total == 1
    if (id_ := payload["defaultCurrencyId"]) is not None:
        assert configuration_raw_response["defaultCurrency"]["id"] == id_
        assert user.default_currency_id == id_
    else:
        assert configuration_raw_response["defaultCurrency"] is None
        assert user.default_currency_id is None
        assert user.default_currency is None

    if (id_ := payload["defaultCostCategoryId"]) is not None:
        assert configuration_raw_response["defaultCostCategory"]["id"] == id_
        assert user.default_cost_category_id == id_
    else:
        assert configuration_raw_response["defaultCostCategory"] is None
        assert user.default_cost_category_id is None
        assert user.default_cost_category is None
