"""
Tests for assets CRUD operations.
"""

import httpx
import pytest
from fastapi import status


# ==================================================
# tests for not authorized
# ==================================================
@pytest.mark.use_db
async def test_assets_list_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.get("/assets")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_assets_create_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post("/assets", json={"name": "BTC"})
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_assets_update_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.patch("/assets/1", json={"name": "ETH"})
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_assets_delete_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.delete("/assets/1")
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_assets_add_field_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post(
        "/assets/1/fields",
        json={"key": "k", "value": "v"},
    )
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


@pytest.mark.use_db
async def test_assets_upload_document_anonymous(
    anonymous: httpx.AsyncClient,
):
    response = await anonymous.post(
        "/assets/1/documents",
        files={"file": ("f.txt", b"data", "text/plain")},
    )
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), response.json()


# ==================================================
# CRUD happy paths — Assets
# ==================================================
@pytest.mark.use_db
async def test_asset_create(
    client: httpx.AsyncClient,
):
    response = await client.post("/assets", json={"name": "BTC"})
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert raw["name"] == "BTC"
    assert raw["fields"] == []
    assert raw["documents"] == []
    assert "id" in raw


@pytest.mark.use_db
async def test_asset_list(
    client: httpx.AsyncClient,
):
    await client.post("/assets", json={"name": "BTC"})
    await client.post("/assets", json={"name": "Apartment"})

    response = await client.get("/assets")
    results = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(results) == 2


@pytest.mark.use_db
async def test_asset_list_empty(
    client: httpx.AsyncClient,
):
    response = await client.get("/assets")
    results = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(results) == 0


@pytest.mark.use_db
async def test_asset_update_name(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.patch(
        f"/assets/{asset_id}", json={"name": "Bitcoin"}
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert raw["name"] == "Bitcoin"


@pytest.mark.use_db
async def test_asset_delete(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.delete(f"/assets/{asset_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it is gone
    list_resp = await client.get("/assets")
    assert len(list_resp.json()["result"]) == 0


@pytest.mark.use_db
async def test_asset_not_found_update(
    client: httpx.AsyncClient,
):
    response = await client.patch("/assets/9999", json={"name": "Nope"})
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@pytest.mark.use_db
async def test_asset_not_found_delete(
    client: httpx.AsyncClient,
):
    response = await client.delete("/assets/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


# ==================================================
# CRUD happy paths — Asset Fields
# ==================================================
@pytest.mark.use_db
async def test_asset_add_field(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.post(
        f"/assets/{asset_id}/fields",
        json={"key": "Amount", "value": "0.5"},
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert len(raw["fields"]) == 1
    assert raw["fields"][0]["key"] == "Amount"
    assert raw["fields"][0]["value"] == "0.5"


@pytest.mark.use_db
async def test_asset_update_field(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    field_resp = await client.post(
        f"/assets/{asset_id}/fields",
        json={"key": "Amount", "value": "0.5"},
    )
    field_id = field_resp.json()["result"]["fields"][0]["id"]

    response = await client.patch(
        f"/assets/{asset_id}/fields/{field_id}",
        json={"value": "1.0"},
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert raw["fields"][0]["value"] == "1.0"
    assert raw["fields"][0]["key"] == "Amount"


@pytest.mark.use_db
async def test_asset_delete_field(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    field_resp = await client.post(
        f"/assets/{asset_id}/fields",
        json={"key": "Amount", "value": "0.5"},
    )
    field_id = field_resp.json()["result"]["fields"][0]["id"]

    response = await client.delete(f"/assets/{asset_id}/fields/{field_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify field is gone
    list_resp = await client.get("/assets")
    assert len(list_resp.json()["result"][0]["fields"]) == 0


@pytest.mark.use_db
async def test_asset_field_not_found(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.delete(f"/assets/{asset_id}/fields/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


# ==================================================
# CRUD happy paths — Asset Documents
# ==================================================
@pytest.mark.use_db
async def test_asset_upload_document(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "Apartment"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.post(
        f"/assets/{asset_id}/documents",
        files={
            "file": (
                "contract.pdf",
                b"%PDF-1.4 fake content",
                "application/pdf",
            )
        },
    )
    raw = response.json()["result"]

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert len(raw["documents"]) == 1
    assert raw["documents"][0]["filename"] == "contract.pdf"
    assert raw["documents"][0]["contentType"] == "application/pdf"


@pytest.mark.use_db
async def test_asset_download_document(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "Apartment"})
    asset_id = create_resp.json()["result"]["id"]

    file_content = b"%PDF-1.4 fake content"
    upload_resp = await client.post(
        f"/assets/{asset_id}/documents",
        files={
            "file": (
                "contract.pdf",
                file_content,
                "application/pdf",
            )
        },
    )
    doc_id = upload_resp.json()["result"]["documents"][0]["id"]

    response = await client.get(f"/assets/{asset_id}/documents/{doc_id}")

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.content == file_content
    assert "application/pdf" in response.headers.get("content-type", "")
    assert "contract.pdf" in response.headers.get("content-disposition", "")


@pytest.mark.use_db
async def test_asset_delete_document(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "Apartment"})
    asset_id = create_resp.json()["result"]["id"]

    upload_resp = await client.post(
        f"/assets/{asset_id}/documents",
        files={
            "file": (
                "contract.pdf",
                b"data",
                "application/pdf",
            )
        },
    )
    doc_id = upload_resp.json()["result"]["documents"][0]["id"]

    response = await client.delete(f"/assets/{asset_id}/documents/{doc_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify document is gone
    list_resp = await client.get("/assets")
    assert len(list_resp.json()["result"][0]["documents"]) == 0


@pytest.mark.use_db
async def test_asset_document_not_found(
    client: httpx.AsyncClient,
):
    create_resp = await client.post("/assets", json={"name": "Apartment"})
    asset_id = create_resp.json()["result"]["id"]

    response = await client.get(f"/assets/{asset_id}/documents/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


# ==================================================
# delete cascade
# ==================================================
@pytest.mark.use_db
async def test_asset_delete_cascades_fields_and_docs(
    client: httpx.AsyncClient,
):
    """Deleting an asset removes its fields and docs."""

    create_resp = await client.post("/assets", json={"name": "BTC"})
    asset_id = create_resp.json()["result"]["id"]

    # Add a field
    await client.post(
        f"/assets/{asset_id}/fields",
        json={"key": "Amount", "value": "0.5"},
    )

    # Upload a document
    await client.post(
        f"/assets/{asset_id}/documents",
        files={
            "file": (
                "receipt.pdf",
                b"binary",
                "application/pdf",
            )
        },
    )

    # Verify they exist
    list_resp = await client.get("/assets")
    asset = list_resp.json()["result"][0]
    assert len(asset["fields"]) == 1
    assert len(asset["documents"]) == 1

    # Delete asset
    response = await client.delete(f"/assets/{asset_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify everything is gone
    list_resp = await client.get("/assets")
    assert len(list_resp.json()["result"]) == 0
