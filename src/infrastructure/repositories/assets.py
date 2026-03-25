from sqlalchemy import Result, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infrastructure import database, errors


class Assets(database.DataAccessLayer):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session)

    async def assets(self) -> list[database.Asset]:
        """Get all assets with fields and document metadata."""

        query: Select = (
            select(database.Asset)
            .options(
                joinedload(database.Asset.fields),
                joinedload(database.Asset.documents).defer(
                    database.AssetDocument.data
                ),
            )
            .order_by(database.Asset.created_at)
        )

        async with self._read_session() as session:
            results: Result = await session.execute(query)
            return list(results.unique().scalars())

    async def asset(self, id_: int) -> database.Asset:
        """Get a single asset by id with fields and documents."""

        query: Select = (
            select(database.Asset)
            .where(database.Asset.id == id_)
            .options(
                joinedload(database.Asset.fields),
                joinedload(database.Asset.documents).defer(
                    database.AssetDocument.data
                ),
            )
        )

        async with self._read_session() as session:
            results: Result = await session.execute(query)
            if not (item := results.unique().scalars().one_or_none()):
                raise errors.NotFoundError(f"Asset {id_} not found")

        return item

    async def add_asset(self, candidate: database.Asset) -> database.Asset:
        """Add a new asset."""

        self._write_session.add(candidate)
        return candidate

    async def update_asset(self, id_: int, **fields) -> None:
        """Update asset fields."""

        query = (
            update(database.Asset)
            .where(database.Asset.id == id_)
            .values(**fields)
        )

        await self._write_session.execute(query)

    async def delete_asset(self, id_: int) -> None:
        """Delete an asset by id (cascades fields + docs)."""

        query = delete(database.Asset).where(database.Asset.id == id_)

        await self._write_session.execute(query)

    # ---------------------------------------------------------
    # Asset Fields
    # ---------------------------------------------------------
    async def asset_field(
        self, asset_id: int, field_id: int
    ) -> database.AssetField:
        """Get a single asset field."""

        query: Select = select(database.AssetField).where(
            database.AssetField.id == field_id,
            database.AssetField.asset_id == asset_id,
        )

        async with self._read_session() as session:
            results: Result = await session.execute(query)
            if not (item := results.scalars().one_or_none()):
                raise errors.NotFoundError(f"Asset field {field_id} not found")

        return item

    async def add_field(
        self, candidate: database.AssetField
    ) -> database.AssetField:
        """Add a new field to an asset."""

        self._write_session.add(candidate)
        return candidate

    async def update_field(self, field_id: int, **fields) -> None:
        """Update an asset field."""

        query = (
            update(database.AssetField)
            .where(database.AssetField.id == field_id)
            .values(**fields)
        )

        await self._write_session.execute(query)

    async def delete_field(self, field_id: int) -> None:
        """Delete an asset field."""

        query = delete(database.AssetField).where(
            database.AssetField.id == field_id
        )

        await self._write_session.execute(query)

    # ---------------------------------------------------------
    # Asset Documents
    # ---------------------------------------------------------
    async def asset_document(
        self, asset_id: int, document_id: int
    ) -> database.AssetDocument:
        """Get a single asset document (with binary data)."""

        query: Select = select(database.AssetDocument).where(
            database.AssetDocument.id == document_id,
            database.AssetDocument.asset_id == asset_id,
        )

        async with self._read_session() as session:
            results: Result = await session.execute(query)
            if not (item := results.scalars().one_or_none()):
                raise errors.NotFoundError(
                    f"Asset document {document_id} not found"
                )

        return item

    async def add_document(
        self, candidate: database.AssetDocument
    ) -> database.AssetDocument:
        """Add a new document to an asset."""

        self._write_session.add(candidate)
        return candidate

    async def delete_document(self, document_id: int) -> None:
        """Delete an asset document."""

        query = delete(database.AssetDocument).where(
            database.AssetDocument.id == document_id
        )

        await self._write_session.execute(query)
