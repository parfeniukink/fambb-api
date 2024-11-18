"""
Right here. You can see a lost John's notes about his daily routine.

Usually, John go for costs, incomes, exchanges, etc...

What about those paths?
1. 'users' - well. For sure ASGI servers know everybody who deal with them
    they have the whole ruleset to communicate with people ```http clients```,
    called "Token Authentication".
    ```
    # HTTP HEADER fro token-based authentication
    Authorization: Bearer JWT_TOKEN
    ```
2. 'costs' - the most frequently used path for John.
    John is shopaholic. He knows about his problem and this is why
    he try to rememberabout all the stuff he buys.
    The 'Cost' is just an information about the 'Deal'.
    John is addicted from costs but does not like them!
3. 'incomes' - unfortunately, not that freequently used path.
    John love incomes the most, but goes there not that often :(
    From here John takes resources to make costs from which he is addicted
4. 'exchanges' - sometimes people need to buy using different currencies.
    For that John goes to the dark street (frontend lane) for money.
    All ASGIs do that, believe me. Nothing to worry about.
5. 'currencies' - actually here John runs if clients need to create another
    yet currency for near incomes/outcomes. Low-frequently used.
6. 'analytics' - John lives planning. For that he can run for analytics.
    With analytics John can see the relation between incomes and outcomes.
    With antlycis he can compare monthes, years of data. On that way John
    often goes for 'equity' information - an information about the current
    state of resources. John can tell people how much money they have.


You can open pages to read more about each John's path:
    src/rest/users.py
    src/rest/currencies.py
    src/rest/costs.py
    src/rest/incomes.py
    src/rest/exchagnes.py
    src/rest/analytics.py
"""

__all__ = (
    "analytics",
    "costs",
    "currencies",
    "exchange",
    "incomes",
    "users",
)


from . import analytics, costs, currencies, exchange, incomes, users
