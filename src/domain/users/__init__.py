"""
This package includes all the user-related domain parts.

Other application logical components are available to be configured
by user. For that, the ``users`` table includes fields that could be treated
as 'configuration' fields.
"""

__all__ = (
    "User",
    "UserConfiguration",
    "UserFlat",
    "UserRepository",
)

from .aggregates import User, UserConfiguration
from .entities import UserConfiguration, UserFlat
from .repository import UserRepository
