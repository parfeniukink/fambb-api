"""
This package encapsulates all the available transactions:
* COST - because of 'costs'
* INCOME - because there are many 'income sources'
* EXCHANGE - because of 'currency exchange'

The 'Transaction' itself stands for a shared instance that
represents shared parameters for all types of operations.

In general, this module is about CURD operations of the next tables:
- currencies
- cost_categories
- costs
- incomes
- exchanges
"""

__all__ = (
    "Cost",
    "CostCategory",
    "Exchange",
    "Income",
    "IncomeSource",
    "OperationType",
    "Transaction",
    "TransactionRepository",
)

from .entities import (
    Cost,
    CostCategory,
    Exchange,
    Income,
    IncomeSource,
    OperationType,
    Transaction,
)
from .repository import TransactionRepository
