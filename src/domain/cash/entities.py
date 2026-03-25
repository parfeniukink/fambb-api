from src.domain.entities import InternalData


class CashBalance(InternalData):
    id: int
    currency_id: int
    balance: int
    step: int


class CashBalanceCandidate(InternalData):
    currency_id: int
    step: int
