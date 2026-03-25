from src.infrastructure import database, repositories


async def get_assets() -> list[database.Asset]:
    """Get all assets."""

    return await repositories.Assets().assets()


async def get_asset(asset_id: int) -> database.Asset:
    """Get a single asset by id."""

    return await repositories.Assets().asset(id_=asset_id)


async def create_asset(name: str) -> database.Asset:
    """Create a new asset."""

    repo = repositories.Assets()
    instance = await repo.add_asset(candidate=database.Asset(name=name))
    await repo.flush()

    return await repo.asset(id_=instance.id)


async def update_asset(asset_id: int, **fields) -> database.Asset:
    """Update an existing asset."""

    repo = repositories.Assets()
    await repo.asset(id_=asset_id)
    await repo.update_asset(id_=asset_id, **fields)
    await repo.flush()

    return await repo.asset(id_=asset_id)


async def delete_asset(asset_id: int) -> None:
    """Delete an asset (cascades fields + documents)."""

    repo = repositories.Assets()
    await repo.asset(id_=asset_id)
    await repo.delete_asset(id_=asset_id)
    await repo.flush()


# ---------------------------------------------------------
# Asset Fields
# ---------------------------------------------------------
async def add_asset_field(
    asset_id: int, key: str, value: str
) -> database.Asset:
    """Add a field to an asset."""

    repo = repositories.Assets()
    await repo.asset(id_=asset_id)
    await repo.add_field(
        candidate=database.AssetField(asset_id=asset_id, key=key, value=value)
    )
    await repo.flush()

    return await repo.asset(id_=asset_id)


async def update_asset_field(
    asset_id: int, field_id: int, **fields
) -> database.Asset:
    """Update an asset field."""

    repo = repositories.Assets()
    await repo.asset_field(asset_id=asset_id, field_id=field_id)
    await repo.update_field(field_id=field_id, **fields)
    await repo.flush()

    return await repo.asset(id_=asset_id)


async def delete_asset_field(asset_id: int, field_id: int) -> None:
    """Delete an asset field."""

    repo = repositories.Assets()
    await repo.asset_field(asset_id=asset_id, field_id=field_id)
    await repo.delete_field(field_id=field_id)
    await repo.flush()


# ---------------------------------------------------------
# Asset Documents
# ---------------------------------------------------------
async def upload_asset_document(
    asset_id: int,
    filename: str,
    content_type: str,
    data: bytes,
) -> database.Asset:
    """Upload a document to an asset."""

    repo = repositories.Assets()
    await repo.asset(id_=asset_id)
    await repo.add_document(
        candidate=database.AssetDocument(
            asset_id=asset_id,
            filename=filename,
            content_type=content_type,
            data=data,
        )
    )
    await repo.flush()

    return await repo.asset(id_=asset_id)


async def download_asset_document(
    asset_id: int, document_id: int
) -> database.AssetDocument:
    """Download a document (with binary data)."""

    return await repositories.Assets().asset_document(
        asset_id=asset_id, document_id=document_id
    )


async def delete_asset_document(asset_id: int, document_id: int) -> None:
    """Delete an asset document."""

    repo = repositories.Assets()
    await repo.asset_document(asset_id=asset_id, document_id=document_id)
    await repo.delete_document(document_id=document_id)
    await repo.flush()
