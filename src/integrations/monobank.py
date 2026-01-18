"""
RESPONSE FROM /personal/client-info

{
  // ...
  "accounts": [
    {
      "id": "kKGVoZuHWzqVoZuH",
      "cashbackType": "UAH",
      "currencyCode": 980,
      // ...
    }
  ],
}

RESPONSE FROM /personal/statement/kKGVoZuHWzqVoZuH/1546304461/1546306461
URL PATH ARGUMENTS:
- account_id
- from (start time for results)
- to (end time for results. skip for today)

[
  {
    "id": "ZuHWzqkKGVo=",
    "time": 1554466347,
    "description": "Some name",
    "amount": -95000,
    "operationAmount": -95000,
    "currencyCode": 980,
    "commissionRate": 0,
    "counterEdrpou": "3096889974",
    "counterIban": "UA898999980000355639201001404",
    "counterName": "ТОВАРИСТВО З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНІСТЮ «ВОРОНА»"
    // ...
  },
  // ...
]
"""

from datetime import date, datetime, timedelta
from typing import Final

import httpx
from pydantic import Field, RootModel

from src.infrastructure import PublicData

BASE_URL: Final = "https://api.monobank.ua"
PERSONAL_INFO_URL: Final = f"{BASE_URL}/personal/client-info"
STATEMENTS_URL: Final = f"{BASE_URL}/statements"


class AccountInfo(PublicData):
    id: str
    currency_code: int


class ClientInfoResponse(PublicData):
    accounts: list[AccountInfo]


class Transaction(PublicData):
    id: str
    time: int
    description: str | None = None
    amount: int
    operation_amount: int | None = None
    currency_code: int
    commission_rate: float | None = None
    counter_edrpou: str | None = None
    counter_iban: str | None = None
    counter_name: str | None = None


StatementResponse = RootModel[list[Transaction]]


class MonobankTransactionsResponse(PublicData):
    accounts: list[AccountInfo] = Field(default_factory=list)
    transactions: list[Transaction] = Field(default_factory=list)


async def fetch_last_transactions(
    api_key: str,
) -> MonobankTransactionsResponse:

    now = datetime.now()
    yesterday = now - timedelta(days=1)

    headers: dict[str, str] = {
        "X-Token": api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        client_info_response = await client.get(
            PERSONAL_INFO_URL, headers=headers
        )

        client_info = ClientInfoResponse(**client_info_response.json())
        all_transactions = []

        for acc in client_info.accounts:
            statement_url = (
                f"{STATEMENTS_URL}"
                f"/{acc.id}"
                f"/{int(now.timestamp())}/{int(yesterday.timestamp())}"
            )
            statement_response = await client.get(
                str(statement_url), headers=headers
            )
            if statement_response.is_success:
                txs = StatementResponse.model_validate(
                    statement_response.json()
                )
                all_transactions.extend(txs.root)

    return MonobankTransactionsResponse(
        accounts=client_info.accounts,
        transactions=all_transactions,
    )


async def get_transactions(
    api_key: str, start: date, end: date
) -> list[Transaction]:
    headers: dict[str, str] = {
        "X-Token": api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        client_info_response = await client.get(
            PERSONAL_INFO_URL, headers=headers
        )
        client_info = ClientInfoResponse(**client_info_response.json())
        all_transactions = []

        start_ts = int(
            datetime.combine(start, datetime.min.time()).timestamp()
        )
        end_ts = int(datetime.combine(end, datetime.min.time()).timestamp())

        for acc in client_info.accounts:
            statement_url = f"{STATEMENTS_URL}/{acc.id}/{start_ts}/{end_ts}"
            statement_response: httpx.Response = await client.get(
                statement_url, headers=headers
            )
            if statement_response.is_success:
                txs = StatementResponse.model_validate(
                    statement_response.json()
                )
                all_transactions.extend(txs.root)

    return all_transactions
