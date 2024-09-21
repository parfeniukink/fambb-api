import itertools
from collections.abc import AsyncGenerator
from datetime import datetime

from src.domain.finances import Currency

from .entities import (
    Cost,
    CostCateogoryFlat,
    CostDBCandidate,
    Currency,
    Exchange,
    Income,
    OperationType,
    Transaction,
)


class TransactionRepository:
    """
    TransactionRepository is a data access entrypoint.
    It allows manage costs, incomes, exchanges.
    Everything that could be treated as a 'Money Transaction'.

    It uses the 'Query Builder' to create SQL queries.
    """

    _mock_currencies = {
        1: Currency(id=1, name="USD", sign="$"),
        2: Currency(id=2, name="UAH", sign="#"),
    }

    _mock_cost_categories = {
        1: CostCateogoryFlat(id=1, name="Food"),
        2: CostCateogoryFlat(id=2, name="Services"),
        3: CostCateogoryFlat(id=3, name="House"),
        4: CostCateogoryFlat(id=4, name="Sport"),
        5: CostCateogoryFlat(id=5, name="Education"),
    }

    _mock_transactions: dict[OperationType, list] = {
        "cost": [
            Cost(
                id=1,
                name="Test cost 1",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=_mock_currencies[1],
                category=_mock_cost_categories[1],
            ),
            Cost(
                id=2,
                name="Test cost 2",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=_mock_currencies[2],
                category=_mock_cost_categories[1],
            ),
            Cost(
                id=3,
                name="Test cost 3",
                value=100_00,
                timestamp=datetime.now(),
                user_id=1,
                currency=_mock_currencies[1],
                category=_mock_cost_categories[3],
            ),
        ],
        "income": [
            Income(
                id=1,
                value=20000,
                name="Test Income 1",
                source="revenue",
                timestamp=datetime.now(),
                user_id=1,
                currency=_mock_currencies[2],
            ),
            Income(
                id=2,
                value=22000,
                name="Test Income 2",
                source="other",
                timestamp=datetime.now(),
                user_id=1,
                currency=_mock_currencies[1],
            ),
        ],
        "exchange": [
            Exchange(
                id=1,
                value=230000,
                timestamp=datetime.now(),
                user_id=1,
                from_currency=_mock_currencies[2],
                to_currency=_mock_currencies[1],
            ),
        ],
    }

    async def filter(
        self,
        operation: OperationType | None,
        currency_id: int | None = None,
        limit: int | None = None,
    ) -> AsyncGenerator[Transaction, None]:
        """
        Params:
            ``operations`` - if set to ``None`` then all types of a transaction
                will be returned.

            ``limit`` - limit output results

        """

        # TODO: build the SQL query base on ``operation``.
        """sql
        SELECT (transaction fields) FROM costs
        WHERE (**filters)
        ORDER BY ``timestamp``
        """

        costs: list[Cost] = self._mock_transactions["cost"]
        incomes: list[Income] = self._mock_transactions["income"]
        exchanges: list[Exchange] = self._mock_transactions["exchange"]

        # TODO: Remove after SQL LIMIT is added
        items_count = 0

        for item in itertools.chain(costs, incomes, exchanges):
            name = (
                item.name
                if isinstance(item, (Income, Cost))
                else "Currency Exchange"
            )

            if isinstance(item, (Income, Cost)):
                item_currency_id = item.currency.id
            else:
                item_currency_id = item.to_currency.id

            if operation is not None:
                _operation = operation
            else:
                if isinstance(item, Income):
                    _operation = "income"
                elif isinstance(item, Cost):
                    _operation = "cost"
                elif isinstance(item, Exchange):
                    _operation = "exchange"
                else:
                    raise Exception(f"Operation {operation} is not available")

            # NOTE: The code-level implementation of a filteration
            # TODO: Removed after SQL LIMIT is added
            if currency_id is not None and currency_id != item_currency_id:
                # skip if a specified value is not in the results
                continue

            if limit is not None and items_count > limit:
                # break if out of the limit
                return

            yield Transaction(
                name=name,
                value=item.value,
                currency=(
                    item.currency
                    if isinstance(item, (Cost, Income))
                    else item.to_currency
                ),
                operation=_operation,
            )

    async def cost_categories(self) -> AsyncGenerator[CostCateogoryFlat, None]:
        for item in self._mock_cost_categories.values():
            yield item

    async def add_cost_category(self, name: str) -> CostCateogoryFlat:
        # TODO: move this validation to the DB level
        for item in TransactionRepository._mock_cost_categories.values():
            if item.name == name:
                raise Exception("This Cost category already exist")

        item = CostCateogoryFlat(
            id=TransactionRepository._mock_cost_categories[-1].id + 1,
            name=name,
        )
        TransactionRepository._mock_cost_categories[item.id] = item

        return item

    async def add_cost(self, candidate: CostDBCandidate) -> Cost:
        last_id = max(
            [
                item.id
                for item in TransactionRepository._mock_transactions["cost"]
            ]
        )

        instance = Cost(
            id=last_id + 1,
            name=candidate.name,
            value=candidate.value,
            timestamp=candidate.timestamp,
            user_id=candidate.user_id,
            currency=self._mock_currencies[candidate.currency_id],
            category=self._mock_cost_categories[3],
        )

        TransactionRepository._mock_transactions["cost"].append(instance)
        print(f"Cost is saved. {instance}")

        return instance
