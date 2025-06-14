"""
This is the Application (Operational) layer that could be treated
as a bridge between the Presentation layer and the rest of the application.

It basically represents all the operations in the whole application on
the top level.

Each component in this layer defines specific operations that are
allowed to be performed by the user of this system in general.
"""

__all__ = (
    "add_cost",
    "add_cost_shortcut",
    "add_income",
    "apply_cost_shortcut",
    "authorize",
    "authorize_with_token",
    "currency_exchange",
    "delete_cost",
    "delete_cost_shortcut",
    "delete_currency_exchange",
    "delete_income",
    "get_cost_shortcuts",
    "get_costs",
    "get_currency_exchanges",
    "get_incomes",
    "notify_about_big_cost",
    "notify_about_income",
    "notify_about_worker",
    "sync_transactions_from_monobank",
    "transactions_basic_analytics",
    "transactions_chart_analytics",
    "update_cost",
    "update_income",
    "user_notifications",
    "user_retrieve",
    "user_update",
)


from .analytics import (
    transactions_basic_analytics,
    transactions_chart_analytics,
)
from .authorization import authorize, authorize_with_token
from .notifications import (
    notify_about_big_cost,
    notify_about_income,
    notify_about_worker,
    user_notifications,
)
from .transactions import (
    add_cost,
    add_cost_shortcut,
    add_income,
    apply_cost_shortcut,
    currency_exchange,
    delete_cost,
    delete_cost_shortcut,
    delete_currency_exchange,
    delete_income,
    get_cost_shortcuts,
    get_costs,
    get_currency_exchanges,
    get_incomes,
    sync_transactions_from_monobank,
    update_cost,
    update_income,
)
from .users import user_retrieve, user_update
