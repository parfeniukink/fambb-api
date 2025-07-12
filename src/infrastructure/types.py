from typing import Literal

# available income sources
IncomeSource = Literal["revenue", "gift", "debt", "other"]

# available banks, supported in the application
Bank = Literal["monobank", "privatbank", "oshchadbank"]
