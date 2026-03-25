from src.infrastructure import database, repositories


async def get_cash_balances() -> list[database.CashBalance]:
    """Get all cash balances."""

    return await repositories.Cash().cash_balances()


async def add_cash_balance(
    currency_id: int,
    step: int,
) -> database.CashBalance:
    """Create a new cash balance card."""

    repo = repositories.Cash()
    instance = await repo.add(
        candidate=database.CashBalance(
            currency_id=currency_id,
            balance=0,
            step=step,
        )
    )
    await repo.flush()

    return await repo.cash_balance(id_=instance.id)


async def update_cash_balance(
    cash_balance_id: int,
    **fields,
) -> database.CashBalance:
    """Update an existing cash balance card."""

    repo = repositories.Cash()
    await repo.cash_balance(id_=cash_balance_id)
    await repo.update(id_=cash_balance_id, **fields)
    await repo.flush()

    return await repo.cash_balance(id_=cash_balance_id)


async def delete_cash_balance(
    cash_balance_id: int,
) -> None:
    """Delete a cash balance card."""

    repo = repositories.Cash()
    await repo.cash_balance(id_=cash_balance_id)
    await repo.delete_cash_balance(id_=cash_balance_id)
    await repo.flush()
