from src.infrastructure.entities import InternalData

from .entities import UserConfiguration, UserFlat


class User(UserFlat):
    """Extended user data object with configuration details."""

    configuration: UserConfiguration
