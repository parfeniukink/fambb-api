import functools

from pydantic import Field

from src.infrastructure import database
from src.infrastructure.responses import PublicData


class AssetCreateBody(PublicData):
    """Request body to create a new asset."""

    name: str = Field(description="Asset name")


class AssetUpdateBody(PublicData):
    """Request body to update an asset."""

    name: str = Field(description="New asset name")


class AssetFieldCreateBody(PublicData):
    """Request body to add a field to an asset."""

    key: str = Field(description="Field key")
    value: str = Field(description="Field value")


class AssetFieldUpdateBody(PublicData):
    """Request body to update an asset field."""

    key: str | None = Field(default=None, description="New field key")
    value: str | None = Field(default=None, description="New field value")


class AssetField(PublicData):
    """Public representation of an asset field."""

    id: int = Field(description="Unique identifier in the system")
    key: str = Field(description="Field key")
    value: str = Field(description="Field value")

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "AssetField":
        raise NotImplementedError(
            f"Can not convert {type(instance)} "
            f"into the {cls.__name__} contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.AssetField):
        return cls(
            id=instance.id,
            key=instance.key,
            value=instance.value,
        )


class AssetDocument(PublicData):
    """Public representation of an asset document
    (metadata only, no binary).
    """

    id: int = Field(description="Unique identifier in the system")
    filename: str = Field(description="Original file name")
    content_type: str = Field(description="MIME type")

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "AssetDocument":
        raise NotImplementedError(
            f"Can not convert {type(instance)} "
            f"into the {cls.__name__} contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.AssetDocument):
        return cls(
            id=instance.id,
            filename=instance.filename,
            content_type=instance.content_type,
        )


class Asset(PublicData):
    """Public representation of an asset with nested
    fields and document metadata.
    """

    id: int = Field(description="Unique identifier in the system")
    name: str = Field(description="Asset name")
    fields: list[AssetField] = Field(default_factory=list)
    documents: list[AssetDocument] = Field(default_factory=list)

    @functools.singledispatchmethod
    @classmethod
    def from_instance(cls, instance) -> "Asset":
        raise NotImplementedError(
            f"Can not convert {type(instance)} "
            f"into the {cls.__name__} contract"
        )

    @from_instance.register
    @classmethod
    def _(cls, instance: database.Asset):
        return cls(
            id=instance.id,
            name=instance.name,
            fields=[AssetField.from_instance(f) for f in instance.fields],
            documents=[
                AssetDocument.from_instance(d) for d in instance.documents
            ],
        )
