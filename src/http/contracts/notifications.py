from src.infrastructure.responses import PublicData


class Notification(PublicData):
    message: str
    level: str
