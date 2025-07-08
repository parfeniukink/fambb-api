from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src import domain
from src import operational as op
from src.infrastructure import (
    OffsetPagination,
    ResponseMulti,
    ResponseMultiPaginated,
    dates,
    get_offset_pagination_params,
)

from ..contracts import (
    CostCreateBody,
    Transaction,
    get_transactions_detail_filter,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
async def transactions(
    filter: domain.transactions.TransactionsFilter = Depends(
        get_transactions_detail_filter
    ),
    pagination: OffsetPagination = Depends(get_offset_pagination_params),
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMultiPaginated[Transaction]:
    """transactions list. includes costs, incomes and exchanges.

    Notes:
        the returned ``total`` value is based on applied filters.
        if the currency is specified - ``total`` might be changed
        so you can rely on data properly.

        if the ``cost_category_id`` is provided - pagination is skipped
    """

    (
        items,
        total,
    ) = await domain.transactions.TransactionRepository().transactions(
        filter=filter, offset=pagination.context, limit=pagination.limit
    )

    if items:
        context: int = pagination.context + len(items)
        left: int = total - context
    else:
        context = 0
        left = 0

    return ResponseMultiPaginated[Transaction](
        result=[Transaction.from_instance(item) for item in items],
        context=context,
        left=left,
    )


# note: mock endpoint (not used at all)
@router.get("/stream")
async def transaction_stream(
    start_date: Annotated[
        date,
        Query(
            description=(
                "the start date of transaction in the analytics. "
                "default value is the first day of the current year"
            ),
            alias="startDate",
            default_factory=dates.first_year_date,
        ),
    ],
    end_date: Annotated[
        date,
        Query(
            description="the end date of transaction in the analytics",
            alias="endDate",
            default_factory=date.today,
        ),
    ],
    _: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Transaction]:
    """analytics charts for annual tracking. not implemented yet"""

    instances: tuple[domain.transactions.Transaction, ...] = (
        await op.transactions_chart_analytics(start_date, end_date)
    )

    return ResponseMulti[Transaction](
        result=[Transaction.from_instance(instance) for instance in instances]
    )


# ─────────────────────────────────────────────────────────
# INTEGRATION WITH BANKS
#
# AVAILABLE BANKS
#   - Monobank
# ─────────────────────────────────────────────────────────
@router.post("/integrations/monobank/sync", status_code=status.HTTP_200_OK)
async def monobank_sync_transactions(
    user: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Transaction]:
    """sync last N-days transactions from monobank with internal database"""

    transactions: list[domain.transactions.Transaction] = (
        await op.sync_transactions_from_monobank(user)
    )

    return ResponseMulti[Transaction](
        result=[Transaction.from_instance(item) for item in transactions]
    )
