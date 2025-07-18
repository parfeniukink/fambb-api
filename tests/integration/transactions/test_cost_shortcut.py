"""
this package includes high-level tests for cost shortcuts operatinos.
"""

import httpx
import pytest
from fastapi import status

from src import domain
from src.infrastructure import database


# ==================================================
# tests for not authorized
# ==================================================
async def test_cost_shortcut_create_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.post("/costs/shortcuts", json={})
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


async def test_cost_shortcut_fetch_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.get("/costs/shortcuts")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


async def test_cost_shortcut_delete_anonymous(anonymous: httpx.AsyncClient):
    response = await anonymous.delete("/costs/shortcuts/1")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


# ==================================================
# tests for authorized user
# ==================================================
@pytest.mark.use_db
@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "Water",
            "value": 100,
            "currencyId": 1,
            "categoryId": 1,
        },
        {
            # with no value
            "name": "Billing",
            "currencyId": 2,
            "categoryId": 2,
        },
    ],
)
async def test_cost_shortcut_create(
    client: httpx.AsyncClient, cost_categories, currencies, payload
):
    response = await client.post("/costs/shortcuts", json=payload)
    total = await domain.transactions.TransactionRepository().count(
        database.CostShortcut
    )
    raw_response: dict = response.json()["result"]

    assert total == 1
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert (
        received_value == 100.0
        if (received_value := raw_response["value"])
        else True  # check if the value is specified
    ), received_value
    assert raw_response["ui"]["positionIndex"] == 1


@pytest.mark.use_db
async def test_cost_shortcut_create_multiple(
    client: httpx.AsyncClient, cost_categories, currencies
):
    """test different ``ui_position_index`` values."""

    payload = {"name": "Water", "categoryId": 1, "currencyId": 2}

    await client.post("/costs/shortcuts", json=payload)
    response = await client.post("/costs/shortcuts", json=payload)
    total = await domain.transactions.TransactionRepository().count(
        database.CostShortcut
    )
    raw_response: dict = response.json()["result"]

    assert total == 2, response.json()
    assert raw_response["ui"]["positionIndex"] == 2


@pytest.mark.use_db
async def test_cost_shortcuts_fetch(
    client: httpx.AsyncClient, cost_shortcut_factory
):
    items = await cost_shortcut_factory(n=5)
    response = await client.get("/costs/shortcuts")

    total = await domain.transactions.TransactionRepository().count(
        database.CostShortcut
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json()["result"]) == len(items) == total


@pytest.mark.use_db
async def test_cost_shortcuts_delete(
    client: httpx.AsyncClient, cost_shortcut_factory
):
    items = await cost_shortcut_factory(n=5)

    response = await client.delete(f"/costs/shortcuts/{items[0].id}")

    total = await domain.transactions.TransactionRepository().count(
        database.CostShortcut
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert total == len(items) - 1


@pytest.mark.use_db
async def test_cost_shortcuts_apply(
    client: httpx.AsyncClient, cost_shortcut_factory, currencies
):
    item, *_ = await cost_shortcut_factory(n=1, value=10000)  # 100.00
    repository = domain.transactions.TransactionRepository()

    response = await client.post(f"/costs/shortcuts/{item.id}")
    raw_response = response.json()["result"]

    total_costs = await repository.count(database.Cost)
    created_instance: database.Cost = await repository.cost(
        id_=raw_response["id"]
    )

    currency: database.Currency = (
        await domain.equity.EquityRepository().currency(id_=item.currency_id)
    )

    assert response.status_code == status.HTTP_201_CREATED, raw_response
    assert total_costs == 1
    assert created_instance.value == item.value, raw_response
    assert currency.equity == currencies[0].equity - item.value


@pytest.mark.use_db
async def test_cost_shortcuts_apply_no_value(
    client: httpx.AsyncClient, cost_shortcut_factory
):
    """it is not allowed to apply the cost shortcut with no value without
    the HTTP body specified.
    """

    item, *_ = await cost_shortcut_factory(n=1)  # no value is specified
    repository = domain.transactions.TransactionRepository()

    response = await client.post(f"/costs/shortcuts/{item.id}")

    total_costs = await repository.count(database.Cost)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert total_costs == 0
