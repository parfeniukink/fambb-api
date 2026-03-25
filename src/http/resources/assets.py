from fastapi import APIRouter, Body, Depends, UploadFile, status
from fastapi.responses import Response as RawResponse

from src import application as op
from src import domain
from src.infrastructure import Response, ResponseMulti

from ..contracts.assets import (
    Asset,
    AssetCreateBody,
    AssetFieldCreateBody,
    AssetFieldUpdateBody,
    AssetUpdateBody,
)

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("")
async def list_assets(
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Asset]:
    """List all assets."""

    items = await op.get_assets()

    return ResponseMulti[Asset](
        result=[Asset.from_instance(item) for item in items]
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_asset(
    _: domain.users.User = Depends(op.authorize),
    body: AssetCreateBody = Body(...),
) -> Response[Asset]:
    """Create a new asset."""

    item = await op.create_asset(name=body.name)

    return Response[Asset](result=Asset.from_instance(item))


@router.patch("/{asset_id}")
async def update_asset(
    asset_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: AssetUpdateBody = Body(...),
) -> Response[Asset]:
    """Update an asset name."""

    item = await op.update_asset(asset_id=asset_id, name=body.name)

    return Response[Asset](result=Asset.from_instance(item))


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_asset(
    asset_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """Delete an asset (cascades fields + documents)."""

    await op.delete_asset(asset_id=asset_id)


@router.post(
    "/{asset_id}/fields",
    status_code=status.HTTP_201_CREATED,
)
async def add_asset_field(
    asset_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: AssetFieldCreateBody = Body(...),
) -> Response[Asset]:
    """Add a field to an asset."""

    item = await op.add_asset_field(
        asset_id=asset_id,
        key=body.key,
        value=body.value,
    )

    return Response[Asset](result=Asset.from_instance(item))


@router.patch("/{asset_id}/fields/{field_id}")
async def update_asset_field(
    asset_id: int,
    field_id: int,
    _: domain.users.User = Depends(op.authorize),
    body: AssetFieldUpdateBody = Body(...),
) -> Response[Asset]:
    """Update an asset field."""

    fields: dict = {}
    if body.key is not None:
        fields["key"] = body.key
    if body.value is not None:
        fields["value"] = body.value

    if not fields:
        raise ValueError("Nothing to update")

    item = await op.update_asset_field(
        asset_id=asset_id,
        field_id=field_id,
        **fields,
    )

    return Response[Asset](result=Asset.from_instance(item))


@router.delete(
    "/{asset_id}/fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_asset_field(
    asset_id: int,
    field_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """Remove a field from an asset."""

    await op.delete_asset_field(asset_id=asset_id, field_id=field_id)


@router.get("/{asset_id}/documents/{document_id}")
async def download_asset_document(
    asset_id: int,
    document_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> RawResponse:
    """Download a document (binary response)."""

    doc = await op.download_asset_document(
        asset_id=asset_id, document_id=document_id
    )

    return RawResponse(
        content=doc.data,
        media_type=doc.content_type,
        headers={
            "content-disposition": (f'attachment; filename="{doc.filename}"'),
        },
    )


@router.post(
    "/{asset_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_asset_document(
    asset_id: int,
    file: UploadFile,
    _: domain.users.User = Depends(op.authorize),
) -> Response[Asset]:
    """Upload a document to an asset."""

    data = await file.read()
    content_type = file.content_type or "application/octet-stream"

    item = await op.upload_asset_document(
        asset_id=asset_id,
        filename=file.filename or "untitled",
        content_type=content_type,
        data=data,
    )

    return Response[Asset](result=Asset.from_instance(item))


@router.delete(
    "/{asset_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_asset_document(
    asset_id: int,
    document_id: int,
    _: domain.users.User = Depends(op.authorize),
) -> None:
    """Remove a document from an asset."""

    await op.delete_asset_document(asset_id=asset_id, document_id=document_id)
