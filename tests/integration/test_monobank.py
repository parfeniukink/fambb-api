from typing import Final

import httpx
import pytest
import respx
from fastapi import status

from src import domain
from src.infrastructure import database
from src.integrations import monobank
from tests.utils import read_json

BASE_URL: Final = "/transactions/integrations/monobank"


# ─────────────────────────────────────────────────────────
# USER CONFIGURATION UPDATE
# ─────────────────────────────────────────────────────────
@pytest.mark.use_db
async def test_user_set_monobank_api_key(john, client):
    payload = {"monobankApiKey": "Test API Key"}
    response: httpx.Response = await client.patch(
        "/identity/users/configuration", json=payload
    )

    raw_response = response.json()["result"]

    async with database.transaction():
        user = await domain.users.UserRepository().user_by_id(john.id)

    assert len(user.bank_metadata) == 1
    assert user.bank_metadata[0].api_key == "Test API Key"
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(raw_response["integrations"]) == 1
    assert (
        raw_response["integrations"].get("monobankApiKeyIsSet") is True
    ), raw_response["integrations"]


@pytest.mark.use_db
async def test_user_update_monobank_api_key(john, client):
    """testing upsert API key (if exists)"""

    repo = domain.users.UserRepository()

    async with database.transaction():
        user = await repo.set_api_key(john.id, "monobank", "initial value")

    response: httpx.Response = await client.patch(
        "/identity/users/configuration",
        json={"monobankApiKey": "Test API Key"},
    )

    raw_response = response.json()["result"]

    async with database.transaction():
        user = await domain.users.UserRepository().user_by_id(john.id)

    assert len(user.bank_metadata) == 1
    assert user.bank_metadata[0].api_key == "Test API Key"
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(raw_response["integrations"]) == 1
    assert (
        raw_response["integrations"].get("monobankApiKeyIsSet") is True
    ), raw_response["integrations"]


@pytest.mark.use_db
async def test_user_remove_monobank_api_key(john, client):
    """testing removing API key (if exists)"""

    repo = domain.users.UserRepository()

    async with database.transaction():
        user = await repo.set_api_key(john.id, "monobank", "initial value")

    response: httpx.Response = await client.patch(
        "/identity/users/configuration", json={"monobankApiKey": None}
    )

    raw_response = response.json()["result"]

    async with database.transaction():
        user = await domain.users.UserRepository().user_by_id(john.id)

    assert len(user.bank_metadata) == 1
    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(raw_response["integrations"]) == 1
    assert (
        raw_response["integrations"].get("monobankApiKeyIsSet") is False
    ), raw_response["integrations"]


# ─────────────────────────────────────────────────────────
# SYNC COSTS FEATURE TESTS
# ─────────────────────────────────────────────────────────
@pytest.mark.use_db
async def test_monobank_sync_UNAUTHORIZED(anonymous):
    response: httpx.Response = await anonymous.post(f"{BASE_URL}/sync")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.use_db
@respx.mock
async def test_monobank_sync_NO_API_KEY(client: httpx.AsyncClient):
    response: httpx.Response = await client.post(f"{BASE_URL}/sync")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.use_db
@respx.mock
async def test_monobank_sync(john, client: httpx.AsyncClient):
    # mock Monobank API
    mock_response_personal_info = read_json(
        "response/monobank_personal_info.json"
    )
    print(monobank.PERSONAL_INFO_URL)
    personal_info_route = respx.get(monobank.PERSONAL_INFO_URL).mock(
        return_value=httpx.Response(
            status.HTTP_200_OK, json=mock_response_personal_info
        )
    )
    mock_response_statement = read_json("response/monobank_statement.json")
    statement_route = respx.route(
        url__regex=rf"{monobank.STATEMENTS_URL}/[\w+]"
    ).mock(
        return_value=httpx.Response(
            status.HTTP_200_OK, json=mock_response_statement
        )
    )

    # set API Key
    async with database.transaction():
        await domain.users.UserRepository().set_api_key(
            john.id, "monobank", "initial value"
        )

    response: httpx.Response = await client.post(f"{BASE_URL}/sync")
    raw_response = response.json()["result"]

    _user = await domain.users.UserRepository().user_by_id(john.id)
    user = domain.users.User.from_instance(_user)
    bank_metadata: domain.users.BankMetadata = user.get_bank_metadata(
        "monobank"
    )

    costs_amount: int = (
        await domain.transactions.TransactionRepository().count(database.Cost)
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert personal_info_route.call_count == 1
    assert statement_route.call_count == 1
    assert bank_metadata.transactions_history is not None
    assert len(bank_metadata.transactions_history) == 1
    assert list(bank_metadata.transactions_history)[0] == (
        mock_response_statement[0]["id"]  # type: ignore
    )
    assert costs_amount == 1
    assert len(raw_response) == 1
