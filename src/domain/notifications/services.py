from typing import Literal

from src.infrastructure import Cache, errors

from .entities import Notification, Notifications


async def notify(
    user_id: int,
    topic: Literal["big_costs", "incomes", "worker"],
    notification: Notification,
):

    if topic not in Notifications.model_fields.keys():
        raise errors.BaseError(
            message=f"notifications topic {topic} is not available"
        )

    async with Cache() as cache:
        try:
            results: dict = await cache.get(
                namespace="fambb_notifications", key=str(user_id)
            )
        except errors.NotFoundError:
            notifications = Notifications()
        else:
            notifications = Notifications(**results)

        topic_notifications: list[Notification] = getattr(notifications, topic)
        topic_notifications.append(notification)

        # update cache instance
        await cache.set(
            namespace="fambb_notifications",
            key=str(user_id),
            value=notifications.model_dump(),
        )
