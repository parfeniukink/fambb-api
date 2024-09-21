import random
from datetime import datetime


class Storage:
    """Just a namespace class."""

    users: dict = {
        1: dict(
            id=1,
            name="John Doe",
            default_currency_id=1,
            default_category_id=None,
            common_costs="Water,Chocolate",
            common_incomes=None,
        ),
        2: dict(
            id=2,
            name="Marry Black",
            default_currency_id=None,
            default_category_id=1,
            common_costs=None,
            common_incomes="Office job",
        ),
    }

    currencies: dict = {
        1: dict(
            id=1,
            name="USD",
            sign="$",
            equity=random.randint(10000, 100000),
        ),
        2: dict(
            id=2,
            name="UAH",
            sign="#",
            equity=random.randint(10000, 100000),
        ),
    }

    cost_categories: dict = {
        1: dict(id=1, name="Food"),
        2: dict(id=2, name="Services"),
        3: dict(id=3, name="House"),
        4: dict(id=4, name="Sport"),
        5: dict(id=5, name="Education"),
    }

    costs: dict = {
        1: dict(
            id=1,
            name="Test cost 1",
            value=100_00,
            timestamp=datetime.now(),
            user_id=1,
            currency_id=2,
            category_id=2,
        ),
        2: dict(
            id=2,
            name="Test cost 2",
            value=100_00,
            timestamp=datetime.now(),
            user_id=1,
            currency_id=2,
            category_id=1,
        ),
        3: dict(
            id=3,
            name="Test cost 3",
            value=100_00,
            timestamp=datetime.now(),
            user_id=1,
            currency_id=2,
            category_id=3,
        ),
    }

    incomes: dict = {
        1: dict(
            id=1,
            value=20000,
            name="Test Income 1",
            source="revenue",
            timestamp=datetime.now(),
            user_id=1,
            currency_id=2,
        ),
        2: dict(
            id=2,
            value=22000,
            name="Test Income 2",
            source="other",
            timestamp=datetime.now(),
            user_id=1,
            currency_id=1,
        ),
    }

    exchange: dict = {
        1: dict(
            id=1,
            value=230000,
            timestamp=datetime.now(),
            user_id=1,
            from_currency_id=2,
            to_currency_id=1,
        ),
    }
