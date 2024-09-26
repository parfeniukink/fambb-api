"""
this package includes high-level tests for Cost operatinos
"""

import httpx
import pytest
from fastapi import status


@pytest.mark.use_db
async def test_cost_categories(client: httpx.AsyncClient, cost_categories):
    response = await client.get("costs/categories")

    assert response.status_code == status.HTTP_200_OK
    assert 
