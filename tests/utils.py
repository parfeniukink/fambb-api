import json
from pathlib import Path
from typing import Any

Result = list[dict] | dict[str, Any]


def read_json(path: str) -> Result:
    # cd tests/mock
    prefix = Path(__file__).parent / "mock"

    with open(prefix / path) as file:
        data: Any = json.load(file)

    if not isinstance(data, list | dict):
        raise ValueError(f"Can not load data of {type(data)} type")
    else:
        return data
