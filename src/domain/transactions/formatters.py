def as_pretty_money(value: int, /, **_) -> float:
    if not isinstance(value, int):
        raise ValueError(f"Such operation is allowed only for integers")
    else:
        return round(value / 100, 2)


def as_cents(value: float, /, **_) -> int:
    """just a simple convert to the integer value representation."""

    if not isinstance(value, float):
        raise ValueError(
            f"Can not convet {value} of type {type(value)} to cents"
        )
    else:
        return int(round(value * 100, 2))
