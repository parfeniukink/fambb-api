"""
Tests for cash balance CRUD operations.
"""

import httpx
import pytest
from fastapi import status

from src.infrastructure import database, repositories


# ==================================================
# fixtures
# ==================================================
@pytest.fixture
async def currencies() -> list[database.Currency]:
    """Create two currencies for testing."""

    repo = repositories.Currency()
    usd = await repo.add_currency(database.Currency(name="USD", sign="$"))
    eur = await repo.add_currency(database.Currency(name="EUR", sign="E"))
    await repo.flush()

    return [usd, eur]


# ==================================================
# tests for not authorized
# ==================================================
@pytest.mark.use_db
async def test_cash_list_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.get("/cash")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_cash_create_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post("/cash", json={})
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_cash_update_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.patch("/cash/1", json={})
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_cash_delete_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.delete("/cash/1")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


# ==================================================
# CRUD happy paths
# ==================================================
@pytest.mark.use_db
async def test_cash_create(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    payload = {
        "currencyId": currencies[0].id,
        "step": 100.00,
    }
    response = await client.post("/cash", json=payload)
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert raw["balance"] == 0.0
    assert raw["step"] == 100.0
    assert raw["currency"]["id"] == currencies[0].id
    assert raw["currency"]["name"] == "USD"


@pytest.mark.use_db
async def test_cash_list(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    # Create two cards
    await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 50.00,
        },
    )
    await client.post(
        "/cash",
        json={
            "currencyId": currencies[1].id,
            "step": 100.00,
        },
    )

    response = await client.get("/cash")
    results = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(results) == 2


@pytest.mark.use_db
async def test_cash_update_balance(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/cash/{card_id}",
        json={"balance": 5400.00},
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert raw["balance"] == 5400.0
    assert raw["step"] == 100.0


@pytest.mark.use_db
async def test_cash_update_step(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/cash/{card_id}",
        json={"step": 50.00},
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert raw["step"] == 50.0


@pytest.mark.use_db
async def test_cash_update_both(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/cash/{card_id}",
        json={"balance": 200.00, "step": 25.00},
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert raw["balance"] == 200.0
    assert raw["step"] == 25.0


@pytest.mark.use_db
async def test_cash_delete(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.delete(f"/cash/{card_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it is gone
    list_resp = await client.get("/cash")
    assert len(list_resp.json()["result"]) == 0


# ==================================================
# unique constraint
# ==================================================
@pytest.mark.use_db
async def test_cash_duplicate_currency(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    """Adding two cards for the same currency should fail."""

    payload = {
        "currencyId": currencies[0].id,
        "step": 100.00,
    }
    await client.post("/cash", json=payload)
    response = await client.post("/cash", json=payload)

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()


# ==================================================
# validation errors
# ==================================================
@pytest.mark.use_db
async def test_cash_balance_below_zero(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    """Balance cannot go below 0."""

    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/cash/{card_id}",
        json={"balance": -1.00},
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()


@pytest.mark.use_db
async def test_cash_step_zero(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    """Step must be positive."""

    response = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 0,
        },
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()


@pytest.mark.use_db
async def test_cash_step_negative(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    """Step must be positive."""

    response = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": -50.00,
        },
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()


@pytest.mark.use_db
async def test_cash_update_step_zero(
    client: httpx.AsyncClient,
    currencies: list[database.Currency],
):
    """Step update to zero should fail."""

    create_resp = await client.post(
        "/cash",
        json={
            "currencyId": currencies[0].id,
            "step": 100.00,
        },
    )
    card_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/cash/{card_id}",
        json={"step": 0},
    )

    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), response.json()
