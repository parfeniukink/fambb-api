"""drop user_id from cash_balances

Revision ID: 896bbba0f324
Revises: f39f0c5d4c46
Create Date: 2026-03-23 23:29:00.405989

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "896bbba0f324"
down_revision: Union[str, None] = "f39f0c5d4c46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("uq_cash_balances_user_id"),
        "cash_balances",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("uq_cash_balances_currency_id"),
        "cash_balances",
        ["currency_id"],
    )
    op.drop_constraint(
        op.f("fk_cash_balances_user_id_users"),
        "cash_balances",
        type_="foreignkey",
    )
    op.drop_column("cash_balances", "user_id")


def downgrade() -> None:
    op.add_column(
        "cash_balances",
        sa.Column(
            "user_id",
            sa.INTEGER(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.create_foreign_key(
        op.f("fk_cash_balances_user_id_users"),
        "cash_balances",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        op.f("uq_cash_balances_currency_id"),
        "cash_balances",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("uq_cash_balances_user_id"),
        "cash_balances",
        ["user_id", "currency_id"],
    )
