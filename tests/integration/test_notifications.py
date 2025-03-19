"""
test notifications that are happening on events.
"""

import asyncio

import httpx
import pytest
from fastapi import status

from src.domain.users import UserRepository
from src.infrastructure.database import transaction
from tests.mock import Cache


@pytest.mark.use_db
async def test_user_notified_about_big_cost(
    currencies, cost_categories, client, john, client_marry
):
    """
    WORKFLOW
        1. John update ``notify_cost_threshold`` configuration
        2. Marry creates the cost with value above the `notify_cost_threshold`
        3. wait for notification to be added to the cache in the background
        4. check notification object is added to the cache
    """

    async with transaction():
        await UserRepository().update_user_configuration(
            user_id=john.id, notify_cost_threshold=100  # cents
        )

    add_cost_response: httpx.Response = await client_marry.post(
        "/costs",
        json={"name": "PS5", "value": 200, "currencyId": 1, "categoryId": 1},
    )

    await asyncio.sleep(0.1)
    cache_len_after_creating_cost = len(
        Cache._data[f"fambb_notifications:{john.id}"]["big_costs"]
    )

    notifications_response = await client.get("/notifications")

    assert (
        add_cost_response.status_code == status.HTTP_201_CREATED
    ), add_cost_response.json()
    assert (
        notifications_response.status_code == status.HTTP_200_OK
    ), notifications_response.json()
    assert cache_len_after_creating_cost == 1, Cache._data
    assert Cache._data == {}
