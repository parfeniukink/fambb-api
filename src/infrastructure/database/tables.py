"""
Database tables.

Notes:
    The Base class represents the SQLAlchemy declarative base class.

    The Each class has a ``Table`` suffix to indicate that it's a table.

    ``Enum(..., native_enum=False)`` is used to create a non-native enum type
    so the value is saved as a string in the database. This is related to
    issues with PostgreSQL custom types which are created if native_enum=True
    is used. Also it affects on tests due to the SQLAlchemy caching system.
"""

import functools
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: E501
            "pk": "pk_%(table_name)s",
        }
    )


class DefaultColumnsMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class User(Base, DefaultColumnsMixin):
    """table includes 'users'.

    params:
        ``name`` - 'john'
        ``token`` - pre-generated string for the access
        ``equity`` - 10000 which is 100$. in CENTS

    notes:
        why there is no password and any other authentication stuff?
        there is no reason to store such information since the user is
        needed only to be displayed as a identifier. also, users number
        is not going to be changed, there is no real reason to provide
        a full OAuth and that's why just a token is used to authorized
        user in the system.

        to create a user just run: ``python -m scripts.create_user``.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(unique=True)
    token: Mapped[str]

    # user configurations
    common_costs: Mapped[str | None] = mapped_column(default=None)
    common_incomes: Mapped[str | None] = mapped_column(default=None)

    default_currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT"), default=None
    )
    default_cost_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("cost_categories.id", ondelete="RESTRICT"), default=None
    )

    default_currency: "Mapped[Currency]" = relationship(
        viewonly=True, lazy="select", foreign_keys=[default_currency_id]
    )
    default_cost_category: "Mapped[CostCategory]" = relationship(
        viewonly=True, lazy="select", foreign_keys=[default_cost_category_id]
    )
    costs: "Mapped[list[Cost]]" = relationship(
        "Cost", viewonly=True, uselist=True
    )
    incomes: "Mapped[list[Income]]" = relationship(
        "Income", viewonly=True, uselist=True
    )
    exchanges: "Mapped[list[Exchange]]" = relationship(
        "Exchange", viewonly=True, uselist=True
    )


class Currency(Base, DefaultColumnsMixin):
    """table includes 'equity and currencies'.

    params:
        ``name`` - 'USD'
        ``sign`` - '$'
        ``equity`` - 10000 which is 100$. in CENTS
    """

    __tablename__ = "currencies"

    name: Mapped[str] = mapped_column(unique=True)
    sign: Mapped[str] = mapped_column(String(1), unique=True)
    equity: Mapped[int] = mapped_column(default=0)

    costs: "Mapped[list[Cost]]" = relationship(
        "Cost", viewonly=True, uselist=True
    )
    incomes: "Mapped[list[Income]]" = relationship(
        "Income", viewonly=True, uselist=True
    )
    exchanges_from: "Mapped[list[Exchange]]" = relationship(
        viewonly=True, uselist=True, foreign_keys="[Exchange.from_currency_id]"
    )
    exchanges_to: "Mapped[list[Exchange]]" = relationship(
        viewonly=True, uselist=True, foreign_keys="[Exchange.to_currency_id]"
    )


class CostCategory(Base, DefaultColumnsMixin):
    """table includes 'cost categories'.

    params:
        ``name`` - '🍔 Food'
    """

    __tablename__ = "cost_categories"

    name: Mapped[str] = mapped_column(unique=True)


class Cost(Base, DefaultColumnsMixin):
    """table includes 'costs'.

    example:
        i spend some money on 'system76 laptop'.

    params:
        ``name`` - 'System76 laptop'
        ``value`` - 180000 which is 1800$. in CENTS
        ``timestamp`` - operation timestamp
        ``user_id`` - operator
        ``category_id`` - cost category id
        ``currency_id`` - operation currency
    """

    __tablename__ = "costs"

    name: Mapped[str] = mapped_column(unique=True)
    value: Mapped[int] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(
        default=functools.partial(datetime.now, UTC),
        onupdate=functools.partial(datetime.now, UTC),
        server_default=func.CURRENT_TIMESTAMP(),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("cost_categories.id", ondelete="RESTRICT")
    )
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )

    user: Mapped[User] = relationship(
        viewonly=True, lazy="select", foreign_keys=[user_id]
    )
    category: Mapped[CostCategory] = relationship(
        viewonly=True, lazy="select", foreign_keys=[category_id]
    )
    currency: Mapped[Currency] = relationship(
        viewonly=True, lazy="select", foreign_keys=[currency_id]
    )


class Income(Base, DefaultColumnsMixin):
    """table includes 'incomes'.

    example:
        i made some money today by teaching students

    params:
        ``name`` - 'teaching'
        ``value`` - 5000 which is 50$. in CENTS
        ``timestamp`` - operation timestamp
        ``source`` - the income source (revenue, gift, ...)
        ``user_id`` - operator
        ``category_id`` - cost category id
        ``currency_id`` - operation currency

    notes:
        why source is not an enum? well, this is because we rely on software
        when handling the source value. the source is a regular string, that is
        represented as a Literal in the ``domain.transactions.constants``.
    """

    __tablename__ = "incomes"

    name: Mapped[str] = mapped_column(unique=True)
    value: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(
        default=functools.partial(datetime.now, UTC),
        onupdate=functools.partial(datetime.now, UTC),
        server_default=func.CURRENT_TIMESTAMP(),
    )
    source: Mapped[str] = mapped_column(unique=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("cost_categories.id", ondelete="RESTRICT")
    )
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )

    user: Mapped[User] = relationship(
        viewonly=True, lazy="select", foreign_keys=[user_id]
    )
    category: Mapped[CostCategory] = relationship(
        viewonly=True, lazy="select", foreign_keys=[category_id]
    )
    currency: Mapped[Currency] = relationship(
        viewonly=True, lazy="select", foreign_keys=[currency_id]
    )


class Exchange(Base, DefaultColumnsMixin):
    """table includes 'currency exchanges'.

    example:
        exchange 100 USD to UAH. below, params are explained.

    params:
        ``from_value`` - 10000 which is 100 USD in CENTS
        ``to_value`` - 400000 if the rate is 40 UAH for 1 USD. in CENTS
        ``timestamp`` - operation timestamp
        ``from_currency`` - 1 if USD has id=1
        ``to_currency`` - 2 if UAH has id=2
    """

    __tablename__ = "exchanges"

    from_value: Mapped[int]
    to_value: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(
        default=functools.partial(datetime.now, UTC),
        onupdate=functools.partial(datetime.now, UTC),
        server_default=func.CURRENT_TIMESTAMP(),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    from_currency_id: Mapped[int] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )
    to_currency_id: Mapped[int] = mapped_column(
        ForeignKey("currencies.id", ondelete="RESTRICT")
    )

    user: Mapped[User] = relationship(
        viewonly=True, lazy="select", foreign_keys=[user_id]
    )
    from_currency: Mapped[Currency] = relationship(
        viewonly=True, lazy="select", foreign_keys=[from_currency_id]
    )
    to_currency: Mapped[Currency] = relationship(
        viewonly=True, lazy="select", foreign_keys=[to_currency_id]
    )
