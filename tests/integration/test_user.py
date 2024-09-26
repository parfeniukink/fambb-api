import httpx
import pytest
from fastapi import status

from src.domain import users as domain
from src.infrastructure import database


@pytest.mark.use_db
async def test_user_retrieve(john, client):
    response: httpx.Response = await client.get("/users")
    result: dict = response.json()["result"]
    users_total = await domain.UserRepository().count(database.User)

    assert response.status_code == status.HTTP_200_OK
    assert result["id"] == john.id
    assert result["name"] == john.name
    assert users_total == 1


@pytest.mark.use_db
async def test_user_retrieve_anonymous(anonymous):
    response: httpx.Response = await anonymous.get("/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
