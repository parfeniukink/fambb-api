"""
SHARED KERNEL.

This component represents the banch of the shared financial operations
for the whole application.
"""

__all__ = (
    "Currency",
    "CurrencyRepository",
    "CurrencyWithEquity",
)

from .entities import Currency, CurrencyWithEquity
from .repository import CurrencyRepository
