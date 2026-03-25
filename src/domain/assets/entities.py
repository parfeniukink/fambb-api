from src.domain.entities import InternalData


class Asset(InternalData):
    id: int
    name: str


class AssetField(InternalData):
    id: int
    asset_id: int
    key: str
    value: str


class AssetFieldCandidate(InternalData):
    key: str
    value: str


class AssetDocument(InternalData):
    id: int
    asset_id: int
    filename: str
    content_type: str
