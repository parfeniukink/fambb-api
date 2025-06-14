"""
REASONING
===========
generate and provide user notifications

FEATURES
===========
- define the meaning of the ``Notification``
- news, suggestions forming using LLM
"""

__all__ = ("Notification", "Notifications", "notify")


from .entities import Notification, Notifications
from .services import notify
