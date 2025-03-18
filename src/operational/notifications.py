"""
since the application is created to be used along with SPA in the browser,
we are going to send notifications to the frontend on regular HTTP Request.

notifications are 'super-low' priority so they are removed right after
client requested notifications.
"""

from src import domain
from src.infrastructure import Cache, database, errors

pretty_money = domain.transactions.data_transformation.pretty_money


async def user_notifications(
    user: domain.users.User,
) -> domain.notifications.Notifications:
    """

    WORKFLOW
        1. retrieve notifications from the cache
        2. remove notifications in the cache
    """

    async with Cache() as cache:
        try:
            results: dict = await cache.get(
                namespace="fambb_notifications", key=str(user.id)
            )
        except errors.NotFoundError:
            notifications = domain.notifications.Notifications()
        else:
            notifications = domain.notifications.Notifications(**results)

            # erase notifications
            await cache.delete(
                namespace="fambb_notifications", key=str(user.id)
            )

        return notifications


async def notify_about_big_cost(cost: database.Cost):
    """add notification if threshold in the confiuration
    is above of the value of the cost
    """

    async for (
        _user
    ) in domain.users.UserRepository().by_cost_threshold_notification(
        cost=cost
    ):
        user = domain.users.User.from_instance(_user)

        async with Cache() as cache:
            try:
                results: dict = await cache.get(
                    namespace="fambb_notifications", key=str(user.id)
                )
            except errors.NotFoundError:
                notifications = domain.notifications.Notifications()
            else:
                notifications = domain.notifications.Notifications(**results)

            # augment instance
            notifications.big_costs.append(
                domain.notifications.Notification(
                    message=(
                        f"{cost.name}: {pretty_money(cost.value)} "
                        f"{cost.currency.sign}"
                    ),
                    level="📉",
                )
            )

            # update cache instance
            await cache.set(
                namespace="fambb_notifications",
                key=str(user.id),
                value=notifications.model_dump(),
            )


async def notify_about_income(income: database.Income):

    user: database.User = await domain.users.UserRepository().excluding(
        income.user_id
    )

    async with Cache() as cache:
        try:
            results: dict = await cache.get(
                namespace="fambb_notifications", key=str(user.id)
            )
        except errors.NotFoundError:
            notifications = domain.notifications.Notifications()
        else:
            notifications = domain.notifications.Notifications(**results)

        # augment instance
        notifications.incomes.append(
            domain.notifications.Notification(
                message=(
                    f"{income.name}: {pretty_money(income.value)} "
                    f"{income.currency.sign}"
                ),
                level="📈",
            )
        )

        # update cache instance
        await cache.set(
            namespace="fambb_notifications",
            key=str(user.id),
            value=notifications.model_dump(),
        )
