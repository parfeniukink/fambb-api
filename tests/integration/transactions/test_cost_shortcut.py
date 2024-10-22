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
            "name": "PS5",
            "value": 100,
            "currencyId": 1,
            "categoryId": 1,
        },
        {
            # with no value
            "name": "PS5",
            "currencyId": 1,
            "categoryId": 1,
        },
    ],
)
async def test_cost_shortcut_create(
    client: httpx.AsyncClient, cost_categories, currencies, payload
):
    response = await client.post(
        "/costs/shortcuts",
        json=payload,
    )

    total = await domain.transactions.TransactionRepository().count(
        database.CostShortcut
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert total == 1


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
