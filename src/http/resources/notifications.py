from fastapi import APIRouter, Depends, status

from src import domain
from src import operational as op
from src.infrastructure import ResponseMulti

from ..contracts import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", status_code=status.HTTP_200_OK)
async def user_notifications(
    user: domain.users.User = Depends(op.authorize),
) -> ResponseMulti[Notification]:
    """Get user notifications"""

    notifications: domain.notifications.Notifications = (
        await op.user_notifications(user)
    )

    results: list[Notification] = []
    results.extend(
        [Notification.model_validate(item) for item in notifications.big_costs]
    )
    results.extend(
        [Notification.model_validate(item) for item in notifications.incomes]
    )

    return ResponseMulti[Notification](result=results)
